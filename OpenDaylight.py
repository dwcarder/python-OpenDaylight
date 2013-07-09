""" 
OpenDaylight REST API 

Copyright 2013 The University of Wisconsin Board of Regents

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.


 Written by: Dale W. Carder, dwcarder@wisc.edu
 Network Services Group
 Division of Information Technology
 University of Wisconsin at Madison

This material is based upon work supported by the National Science Foundation 
under Grant No.  1247322. 
"""

from __future__ import print_function
import json
import requests
from requests.auth import HTTPBasicAuth

class OpenDaylight(object):
    """An object holding details to talk to the OpenDaylight REST API

       OpenDaylight.setup is a dictionary loaded with the following
       default values:
          {'hostname':'localhost',
           'port':'8080',
           'username':'admin',
           'password':'admin',
           'path':'/controller/nb/v2/',
           'container':'default',
           'http':'http://' }

       Your code should change these as required for your installation.
       OpenDaylight.url holds the url for each REST query.  Typically
       you would let OpenDaylight.prepare() build this for you.

       OpenDaylight.auth holds an auth object for Requests to use 
       for each REST query.  Typically you would also let 
       OpenDaylight.prepare() build this for you.
    """

    def __init__(self):
        """Set some mostly reasonable defaults.
        """
        self.setup = {'hostname':'localhost',
                      'port':'8080',
                      'username':'admin',
                      'password':'admin',
                      'path':'/controller/nb/v2/',
                      'container':'default',
                      'http':'http://'}

        self._base_url = None
        self.url = None 
        self.auth = None

    def prepare(self, app, path):
        """Sets up the necessary details for the REST connection by calling
           prepare_url and prepare_auth.  

           Arguments:
            'app'  - which OpenDaylight northbound api component (application)
                     we want to talk to.
            'path' - the specific rest query for the application.
        """
        self.prepare_url(app, path)
        self.prepare_auth()

    def prepare_url(self, app, path):
        """Build the URL for this REST connection which is then stored as
           OpenDaylight.url

           If you use prepare(), you shouldn't need to call prepare_url() 
           yourself.  However, if there were a URL you wanted to construct that 
           was so whacked out custom, then by all means build it yourself and don't
           bother to call this function.  

           Arguments:
            'app'  - which OpenDaylight northbound api component (application)
                     we want to talk to.
            'path' - the specific rest query for the application.

           Note that other attributes, including 'container' are specified
           in the OpenDaylight.setup dictionary.
        """

        # the base url we will use for the connection
        self._base_url = self.setup['http'] + self.setup['hostname'] + ':' + \
                         self.setup['port'] + self.setup['path']

        # the specific path we are building
        self.url = self._base_url + app + '/' + self.setup['container'] + path

    def prepare_auth(self):
        """Set up the credentials for the REST connection by creating
           an auth object for Requests and shoving it into OpenDaylight.auth

           Currently, as far as I know, the OpenDaylight controller uses
           http basic auth.  If/when that changes this function should be
           updated.

           If you use prepare(), you shouldn't need to call prepare_auth() 
           yourself.  However, if there were something you wanted to do
           that was so whacked out custom, then by all means build it yourself 
           and don't bother to call this function.  
        """

        # stuff an HTTPBasicAuth object in here ready for use
        self.auth = HTTPBasicAuth(self.setup['username'], 
                                  self.setup['password'])
        #print("Prepare set up auth: " + self.setup['username'] + ', ' + \
        #      self.setup['password'])


class OpenDaylightFlow(object):
    """OpenDaylightFlow is an object that talks to the OpenDaylight 
       Flow Programmer application REST API

       OpenDaylight.odl holds an OpenDaylight object containing details
       on how to communicate with the controller.

       OpenDaylightFlow.request holds a Requests object for the REST
       session.  Take a look at the Requests documentation for all of
       the methods available, but here are a few handy examples:
          OpenDaylightFlow.request.status_code  - returns the http code
          OpenDaylightFlow.request.text    - returns the response as text

       OpenDaylightFlow.flows holds a dictionary that corresponds to
       the flowConfig element in the OpenDaylight REST API.  Note that
       we don't statically define what those fields are here in this
       object.  This makes this library code more flexible as flowConfig 
       changes over time.  After all, this is REST, not RPC.
    """

    def __init__(self, odl):
        """Mandatory argument: 
            odl      - an OpenDaylight object
        """
        self.odl = odl
        self.__app = 'flow'
        self.request = None
        self.flows = None

    def get(self, node_id=None, flow_name=None):
        """Get Flows specified on the Controller and stuffs the results into
           the OpenDaylightFlow.flows dictionary.

             Optional Arguments: 
                node_id     -   returns flows just for that switch dpid
                flow_name   -   returns the specifically named flow on that switch
        """

        # clear out any remaining crud from previous calls
        if hasattr(self, 'request'):
            del self.request
        if hasattr(self, 'flows'):
            del self.flows

        if node_id is None:
            self.odl.prepare(self.__app, '/')
        elif flow_name is None:
            self.odl.prepare(self.__app, '/' + 'OF/' + node_id + '/')
        else:
            self.odl.prepare(self.__app, '/' + 'OF/' + node_id + '/' 
                         + flow_name + '/')

        self.request = requests.get(url=self.odl.url, auth=self.odl.auth)

        if self.request.status_code == 200:
            self.flows = self.request.json()
            if 'flowConfig' in self.flows:
                self.flows = self.flows.get('flowConfig')
        else:
            raise OpenDaylightError({'url':self.odl.url, 
                                     'http_code':self.request.status_code,
                                     'msg':self.request.text})


    def add(self, flow):
        """Given a dictionary corresponding to a flowConfig, add this flow to 
           the Controller.  Note that the switch dpid and the flow's name is
           specified in the flowConfig passed in.
        """
        if hasattr(self, 'request'):
            del self.request
        #print(flow)
        self.odl.prepare(self.__app, '/' + flow['node']['@type'] + '/' + 
                     flow['node']['@id'] + '/' + flow['name'] + '/')
        headers = {'Content-type': 'application/json'}
        body = json.dumps(flow)
        self.request = requests.post(url=self.odl.url, auth=self.odl.auth,
                                     data=body, headers=headers)

        if self.request.status_code != 201:
            raise OpenDaylightError({'url':self.odl.url, 
                                     'http_code':self.request.status_code,
                                     'msg':self.request.text})

    #def update(self):
    #    """Update a flow to a Node on the Controller
    #    """
    #    raise NotImplementedError("update()")

    def delete(self, node_id, flow_name):
        """Delete a flow to a Node on the Controller

           Mandatory Arguments: 
              node_id     -   the switch dpid
              flow_name   -   the specifically named flow on that switch
        """
        if hasattr(self, 'request'):
            del self.request

        self.odl.prepare(self.__app, '/' + 'OF/' + node_id + '/' + 
                         flow_name + '/')
        self.request = requests.delete(url=self.odl.url, auth=self.odl.auth)

        # note, if you wanted to pass in a flowConfig style dictionary, 
        # this is how you would do it.  This is what I did initially, but 
        # it seemed clunky to pass in an entire flow.
        #self.prepare(self.__app, '/' + flow['node']['@type'] + '/' + 
        #             flow['node']['@id'] + '/' + flow['name'] + '/')

        if self.request.status_code != 200:
            raise OpenDaylightError({'url':self.odl.url, 
                                     'http_code':self.request.status_code,
                                     'msg':self.request.text})


#pylint: disable=R0921
class OpenDaylightNode(object):
    """A way to talk to the OpenDaylight Switch Manager REST API

       OpenDaylight.odl holds an OpenDaylight object containing details
       on how to communicate with the controller.

       OpenDaylightNode.request holds a Requests object for the REST
       session.  Take a look at the Requests documentation for all of
       the methods available, but here are a few handy examples:
          OpenDaylightNode.request.status_code  - returns the http code
          OpenDaylightNode.request.text    - returns the response as text

       OpenDaylightNode.nodes holds a dictionary that corresponds to
       the 'nodes' element in the OpenDaylight REST API.  

       OpenDaylightNode.node_connectors holds a dictionary that corresponds to
       the 'nodeConnectors' element in the OpenDaylight REST API.  

       Note that we don't statically define what those fields are contained
       in the 'nodes' or 'nodeConnectors' elements here in this object.  
    """

    # Just a note that there are more functions available on 
    # the controller that could be implemented, but it is not
    # clear at this time if that is useful

    def __init__(self, odl):
        """Mandatory argument:
            odl - an OpenDaylight object
        """
        self.odl = odl
        self.__app = 'switch'
        self.nodes = None
        self.node_connectors = None
        self.request = None

    def get_nodes(self):
        """Get information about Nodes on the Controller and stuffs the
           result into the OpenDaylightNode.notes dictionary.

        """
        if hasattr(self, 'request'):
            del self.request
        if hasattr(self, 'nodes'):
            del self.nodes

        self.odl.prepare(self.__app, '/nodes/')
        self.request = requests.get(url=self.odl.url, auth=self.odl.auth)

        if self.request.status_code == 200:
            self.nodes = self.request.json()
            if 'nodeProperties' in self.nodes:
                self.nodes = self.nodes.get('nodeProperties')
        else:
            raise OpenDaylightError({'url':self.odl.url, 
                                     'http_code':self.request.status_code,
                                     'msg':self.request.text})

    def get_node_connectors(self, node_id):
        """Get information about NodeConnectors on the Controller and stuffs the
           result into the OpenDaylightNode.node_connectors dictionary.

            Mandatory Arguments: 
                node_id     -   returns flows just for that switch dpid
        """

        if hasattr(self, 'request'):
            del self.request
        if hasattr(self, 'node_connectors'):
            del self.node_connectors

        self.odl.prepare(self.__app, '/node/' + 'OF/' + node_id + '/')
        self.request = requests.get(url=self.odl.url, auth=self.odl.auth)
        if self.request.status_code == 200:
            self.node_connectors = self.request.json()
            if 'nodeConnectorProperties' in self.node_connectors:
                self.node_connectors = self.node_connectors.get(
                                        'nodeConnectorProperties')
        else:
            raise OpenDaylightError({'url':self.odl.url, 
                                     'http_code':self.request.status_code,
                                     'msg':self.request.text})

    def save(self):
        """Save current switch configurations

           The REST API documentation says:
            "Save the current switch configurations", but I am not sure what
            that actually means.  If you think you do, then here you go.
        """

        if hasattr(self, 'request'):
            del self.request

        self.odl.prepare(self.__app, '/switch-config/')
        self.request = requests.post(url=self.odl.url, auth=self.odl.auth)
        if self.request.status_code != 200:
            raise OpenDaylightError({'url':self.odl.url, 
                                     'http_code':self.request.status_code,
                                     'msg':self.request.text})

    def delete_node_property(self):
        """Delete a property of a Node on the Controller
        """
        raise NotImplementedError("delete_node_property()")

    def add_node_property(self):
        """Add a property of a Node on the Controller
        """
        raise NotImplementedError("add_node_property()")

    def delete_node_connector_property(self):
        """Delete a property of a Node on the Controller
        """
        raise NotImplementedError("delete_node_connector_property()")

    def add_node_connector_property(self):
        """Add a property of a Node on the Controller
        """
        raise NotImplementedError("add_node_connector_property()")


class OpenDaylightError(Exception):
    """OpenDaylight Exception Class
    """
    pass
