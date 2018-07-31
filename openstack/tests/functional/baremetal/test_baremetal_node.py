# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from openstack import exceptions
from openstack.tests.functional import base


class TestBareMetalNode(base.BaseFunctionalTest):

    node_id = None

    def setUp(self):
        super(TestBareMetalNode, self).setUp()
        self.require_service('baremetal')

    def tearDown(self):
        if self.node_id:
            self.conn.baremetal.delete_node(self.node_id, ignore_missing=True)
        super(TestBareMetalNode, self).tearDown()

    def test_node_create_get_delete(self):
        node = self.conn.baremetal.create_node(driver='fake-hardware',
                                               name='node-name')
        self.node_id = node.id
        self.assertIsNotNone(self.node_id)

        self.assertEqual(node.name, 'node-name')
        self.assertEqual(node.driver, 'fake-hardware')
        self.assertEqual(node.provision_state, 'available')
        self.assertFalse(node.is_maintenance)

        # NOTE(dtantsur): get_node and find_node only differ in handing missing
        # nodes, otherwise they are identical.
        for call, ident in [(self.conn.baremetal.get_node, self.node_id),
                            (self.conn.baremetal.get_node, 'node-name'),
                            (self.conn.baremetal.find_node, self.node_id),
                            (self.conn.baremetal.find_node, 'node-name')]:
            found = call(ident)
            self.assertEqual(node.id, found.id)
            self.assertEqual(node.name, found.name)

        nodes = self.conn.baremetal.nodes()
        self.assertIn(node.id, [n.id for n in nodes])

        self.conn.baremetal.delete_node(node, ignore_missing=False)
        self.assertRaises(exceptions.NotFoundException,
                          self.conn.baremetal.get_node, self.node_id)

    def test_node_create_in_enroll_provide(self):
        node = self.conn.baremetal.create_node(driver='fake-hardware',
                                               provision_state='enroll')
        self.node_id = node.id

        self.assertEqual(node.driver, 'fake-hardware')
        self.assertEqual(node.provision_state, 'enroll')
        self.assertIsNone(node.power_state)
        self.assertFalse(node.is_maintenance)

        self.conn.baremetal.set_node_provision_state(node, 'manage',
                                                     wait=True)
        self.assertEqual(node.provision_state, 'manageable')

        self.conn.baremetal.set_node_provision_state(node, 'provide',
                                                     wait=True)
        self.assertEqual(node.provision_state, 'available')

    def test_node_negative_non_existing(self):
        uuid = "5c9dcd04-2073-49bc-9618-99ae634d8971"
        self.assertRaises(exceptions.NotFoundException,
                          self.conn.baremetal.get_node, uuid)
        self.assertRaises(exceptions.NotFoundException,
                          self.conn.baremetal.find_node, uuid,
                          ignore_missing=False)
        self.assertRaises(exceptions.NotFoundException,
                          self.conn.baremetal.delete_node, uuid,
                          ignore_missing=False)
        self.assertIsNone(self.conn.baremetal.find_node(uuid))
        self.assertIsNone(self.conn.baremetal.delete_node(uuid))
