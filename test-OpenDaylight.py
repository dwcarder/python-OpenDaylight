#!/usr/bin/python
"""
Tests for the OpenDaylight REST API interface

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

This material is based upon work supported by the National Science 
Foundation under Grant No. 1247322
"""

import time
import unittest
from OpenDaylight import OpenDaylight
from OpenDaylight import OpenDaylightFlow
from OpenDaylight import OpenDaylightNode
from OpenDaylight import OpenDaylightError
from mininet.net import Mininet
#from mininet.util import dumpNodeConnections
#from mininet.log import setLogLevel
from mininet.topo import Topo
from mininet.node import RemoteController

# Edit these as necessary for your organization
CONTROLLER = '10.10.10.1'
USERNAME = 'admin'
PASSWORD = 'admin'
SWITCH_1 = '99:99:99:00:00:00:01:00'
# This is chosen so that it does not conflict with any other
# switches that may be associated to a controller that is not
# dedicated explicitly for testing

class TestSequenceFunctions(unittest.TestCase):
    """Tests for OpenDaylight

       At this point, tests for OpenDaylightFlow and OpenDaylightNode
       are intermingled.  These could be seperated out into seperate
       suites.
    """

    def setUp(self):
        odl = OpenDaylight()
        odl.setup['hostname'] = CONTROLLER
        odl.setup['username'] = USERNAME
        odl.setup['password'] = PASSWORD
        self.flow = OpenDaylightFlow(odl)
        self.node = OpenDaylightNode(odl)

        self.switch_id_1 = SWITCH_1

        self.odl_test_flow_1 = {u'actions': u'DROP',
           u'etherType': u'0x800',
           u'ingressPort': u'1',
           u'installInHw': u'true',
           u'name': u'odl-test-flow1',
           u'node': {u'@id': self.switch_id_1, u'@type': u'OF'},
           u'priority': u'500'}

        self.odl_test_flow_2 = {u'actions': u'DROP',
           u'etherType': u'0x800',
           u'ingressPort': u'2',
           u'installInHw': u'true',
           u'name': u'odl-test-flow2',
           u'node': {u'@id': self.switch_id_1, u'@type': u'OF'},
           u'priority': u'500'}


    def test_01_delete_flows(self):
        """Clean up from any previous test run, just delete these
            flows if they exist.
        """
        try:
            self.flow.delete(self.odl_test_flow_1['node']['@id'],
                             self.odl_test_flow_1['name'])
        except:
            pass

        try:
            self.flow.delete(self.odl_test_flow_2['node']['@id'],
                             self.odl_test_flow_2['name'])
        except:
            pass

    def test_10_add_flow(self):
        """Add a sample flow onto the controller
        """
        self.flow.add(self.odl_test_flow_1)
        self.assertEqual(self.flow.request.status_code, 201)

    def test_10_add_flow2(self):
        """Add a sample flow onto the controller
        """
        self.flow.add(self.odl_test_flow_2)
        self.assertEqual(self.flow.request.status_code, 201)

    def test_15_add_flow2(self):
        """Add a duplicate flow onto the controller
        """
        try:
            self.flow.add(self.odl_test_flow_2)
        except OpenDaylightError:
            pass
        except e:
            self.fail('Unexpected exception thrown:', e)
        else:
            self.fail('Expected Exception not thrown')

    def test_20_get_flow(self):
        """Retrieve the specific flow back from the controller
        """
        self.flow.get(node_id=self.switch_id_1, flow_name='odl-test-flow1')
        self.assertEqual(self.flow.flows, self.odl_test_flow_1)
        self.assertEqual(self.flow.request.status_code, 200)

    def test_20_get_flow2(self):
        """Retrieve the specific flow back from the controller
        """
        self.flow.get(node_id=self.switch_id_1, flow_name='odl-test-flow1')
        self.assertEqual(self.flow.flows, self.odl_test_flow_1)
        self.assertEqual(self.flow.request.status_code, 200)


    def test_30_get_all_switch_flows(self):
        """Retrieve all flows from this switch back from the controller
        """
        self.flow.get(node_id=self.switch_id_1)
        self.assertTrue(self.odl_test_flow_1 in self.flow.flows)
        self.assertTrue(self.odl_test_flow_2 in self.flow.flows)
        self.assertEqual(self.flow.request.status_code, 200)

    def test_30_get_all_flows(self):
        """Retrieve all flows back from the controller
        """
        self.flow.get()
        self.assertTrue(self.odl_test_flow_1 in self.flow.flows)
        self.assertTrue(self.odl_test_flow_2 in self.flow.flows)
        self.assertEqual(self.flow.request.status_code, 200)

    def test_30_get_flows_invalid_switch(self):
        """Try to get a flow from a non-existant switch
        """
        try:
            # This dpid is specifically chosen figuring that it 
            # would not be in use in a production system.  Plus, I
            # simply just like the number 53.
            self.flow.get(node_id='53:53:53:53:53:53:53:53')
        except OpenDaylightError:
            pass
        except e:
            self.fail('Unexpected exception thrown:', e)
        else:
            self.fail('Expected Exception not thrown')

    def test_40_get_flows_invalid_flowname(self):
        """Try to get a flow that does not exist.
        """
        try:
            self.flow.get(node_id=self.switch_id_1, flow_name='foo-foo-foo-bar')
        except OpenDaylightError:
            pass
        except e:
            self.fail('Unexpected exception thrown:', e)
        else:
            self.fail('Expected Exception not thrown')

    def test_50_delete_flow(self):
        """Delete flow 1.
        """
        self.flow.delete(self.odl_test_flow_1['node']['@id'],
                         self.odl_test_flow_1['name'])
        self.assertEqual(self.flow.request.status_code, 200)


    def test_51_deleted_flow_get(self):
        """Verify that the deleted flow does not exist.
        """
        try:
            self.flow.get(node_id=self.switch_id_1, flow_name='odl-test-flow1')
        except OpenDaylightError:
            pass
        except e:
            self.fail('Unexpected exception thrown:', e)
        else:
            self.fail('Expected Exception not thrown')

    def test_55_delete_flow2(self):
        """Delete flow 2
        """
        self.flow.delete(self.odl_test_flow_2['node']['@id'],
                         self.odl_test_flow_2['name'])
        self.assertEqual(self.flow.request.status_code, 200)


    #TODO:  Add invalid flow that has a bad port 
    #TODO:  Add invalid flow that has a non-existant switch 
    #TODO:  Add invalid flow that has an invalid switch name (non-hexadecimal), 
    #       see https://bugs.opendaylight.org/show_bug.cgi?id=27

    def test_60_get_all_nodes(self):
        """Get all of the nodes on the controller

           TODO: verify that SWITCH_1 is contained in the response
        """
        self.node.get_nodes()
        self.assertEqual(self.node.request.status_code, 200)

    def test_60_get_node_connector(self):
        """Retrieve a list of all the node connectors and their properties 
           in a given node 

           TODO: verify that SWITCH_1 is contained in the response
        """
        self.node.get_node_connectors(SWITCH_1)
        self.assertEqual(self.node.request.status_code, 200)


    def test_60_get_bad_node_connector(self):
        """Retrieve a list of all the node connectors and their properties 
           in a given node for a node that does not exist
        """
        try:
            self.node.get_node_connectors('53:53:53:53:53:53:53:53')
        except OpenDaylightError:
            pass
        except e:
            self.fail('Unexpected exception thrown:', e)
        else:
            self.fail('Expected Exception not thrown')


    def test_60_save(self):
        """Save the switch configurations.  
            It's not clear that this can be easily tested, so we just
            see if this call works or not based on the http status code.
        """
        self.node.save()
        self.assertEqual(self.node.request.status_code, 200)


class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."
    def __init__(self, n=2, **opts):
        # Initialize topology and default options
        Topo.__init__(self, **opts)
        # mininet/ovswitch does not want ':'s in the dpid
        switch_id = SWITCH_1.translate(None, ':')
        switch = self.addSwitch('s1', dpid=switch_id)
        # Python's range(N) generates 0..N-1
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            self.addLink(host, switch)

def setup_mininet_simpleTest():
    "Create and test a simple network"
    topo = SingleSwitchTopo(n=4)
    #net = Mininet(topo)
    net = Mininet( topo=topo, controller=lambda name: RemoteController( 
                   name, ip=CONTROLLER ) )
    net.start()
    #print "Dumping host connections"
    #dumpNodeConnections(net.hosts)

    #time.sleep(300)

    #print "Testing network connectivity"
    #net.pingAll()
    #net.stop()

if __name__ == '__main__':
    # Tell mininet to print useful information
    #setLogLevel('info')

    setup_mininet_simpleTest()
    time.sleep(10)
    unittest.main()


