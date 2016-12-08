# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Rackspace Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pprint

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base

CONF = config.CONF


class PoolTestJSON(base.BaseTestCase):
    """Loadbalancer Tempest tests.

    Tests the following operations in the Neutron-LBaaS API using the
    REST client for Load Balancers with default credentials:

        create detached pool
        create shared pool
        delete shared pool
        delete detached pool
    """

    @classmethod
    def resource_setup(cls):
        """Setup client fixtures for test suite."""
        super(PoolTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('lbaas', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(network_name)
        cls.subnet = cls.create_subnet(cls.network)
        cls.create_lb_kwargs = {'tenant_id': cls.subnet['tenant_id'],
                                'vip_subnet_id': cls.subnet['id']}
        cls.load_balancer = \
            cls._create_active_load_balancer(**cls.create_lb_kwargs)
        cls.load_balancer_id = cls.load_balancer['id']

        # get an RPC client for calling into driver
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @classmethod
    def resource_cleanup(cls):
        super(PoolTestJSON, cls).resource_cleanup()

    @test.attr(type='smoke')
    def test_create_shared_pools(self):

        # create detached pool -- no listeners
        shared_pool_kwargs = {'loadbalancer_id': self.load_balancer_id,
                              'protocol': 'HTTP',
                              'description': 'Shared pool',
                              'lb_algorithm': 'ROUND_ROBIN'}
        shared_pool = self._create_pool(**shared_pool_kwargs)

        # create first listener for pool
        first_listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                                 'default_pool_id': shared_pool['id'],
                                 'description': 'First Listener',
                                 'protocol': 'HTTP',
                                 'protocol_port': 80}
        first_listener = self._create_listener(**first_listener_kwargs)
        self.addCleanup(self._delete_listener, first_listener['id'])

        # create second listener for same pool
        second_listener_kwargs = first_listener_kwargs
        second_listener_kwargs['protocol_port'] = 8080
        second_listener_kwargs['description'] = 'Second Listener'
        second_listener = self._create_listener(**second_listener_kwargs)
        self.addCleanup(self._delete_listener, second_listener['id'])

        res = self.client.call(self.context, 'get_service_by_loadbalancer_id',
                               loadbalancer_id=self.load_balancer_id)

        pool = res['pools'][0]
        self.assertEqual(pool['id'], shared_pool['id'])

        # validate pool has two listeners
        listeners = pool['listeners']
        self.assertEqual(2, len(listeners))

        # validate pool/listener relationship
        assert((listeners[0]['id'] == first_listener['id'] and
                listeners[1]['id'] == second_listener['id']) or
               (listeners[0]['id'] == second_listener['id'] and
                listeners[1]['id'] == first_listener['id']))

        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(res)

        # delete shared pool
        self._delete_pool(shared_pool['id'], wait=True)
        res = self.client.call(self.context, 'get_service_by_loadbalancer_id',
                               loadbalancer_id=self.load_balancer_id)

        # validate listeners not associated with a pool
        self.assertEqual(0, len(res['pools']))
        for listener in res['listeners']:
            self.assertIsNone(listener['default_pool_id'])


@test.attr(type='smoke')
def test_create_shared_pools(self):
    # create detached pool -- no listeners
    shared_pool_kwargs = {'loadbalancer_id': self.load_balancer_id,
                          'protocol': 'HTTP',
                          'description': 'Shared pool',
                          'lb_algorithm': 'ROUND_ROBIN'}
    shared_pool = self._create_pool(**shared_pool_kwargs)

    # create first listener for pool
    first_listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                             'default_pool_id': shared_pool['id'],
                             'description': 'First Listener',
                             'protocol': 'HTTP',
                             'protocol_port': 80}
    first_listener = self._create_listener(**first_listener_kwargs)
    self.addCleanup(self._delete_listener, first_listener['id'])

    # create second listener for same pool
    second_listener_kwargs = first_listener_kwargs
    second_listener_kwargs['protocol_port'] = 8080
    second_listener_kwargs['description'] = 'Second Listener'
    second_listener = self._create_listener(**second_listener_kwargs)
    self.addCleanup(self._delete_listener, second_listener['id'])

    res = self.client.call(self.context, 'get_service_by_loadbalancer_id',
                           loadbalancer_id=self.load_balancer_id)

    pool = res['pools'][0]
    self.assertEqual(pool['id'], shared_pool['id'])

    # validate pool has two listeners
    listeners = pool['listeners']
    self.assertEqual(2, len(listeners))

    # validate pool/listener relationship
    assert ((listeners[0]['id'] == first_listener['id'] and
             listeners[1]['id'] == second_listener['id']) or
            (listeners[0]['id'] == second_listener['id'] and
             listeners[1]['id'] == first_listener['id']))

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(res)

    # delete shared pool
    self._delete_pool(shared_pool['id'], wait=True)
    res = self.client.call(self.context, 'get_service_by_loadbalancer_id',
                           loadbalancer_id=self.load_balancer_id)

    # validate listeners not associated with a pool
    self.assertEqual(0, len(res['pools']))
    for listener in res['listeners']:
        self.assertIsNone(listener['default_pool_id'])

    @test.attr(type='smoke')
    def test_create_shared_nodes(self):

        # create first listener
        first_listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                                 'protocol': 'HTTP',
                                 'protocol_port': 80}
        first_listener = self._create_listener(**first_listener_kwargs)
        self.addCleanup(self._delete_listener, first_listener['id'])

        # create first pool
        first_pool_kwargs = {'listener_id': first_listener['id'],
                             'protocol': 'HTTP',
                             'lb_algorithm': 'ROUND_ROBIN'}
        first_pool = self._create_pool(**first_pool_kwargs)

        # create first member
        member_kwargs = {'address': '10.1.4.1',
                         'protocol_port': 8080,
                         'subnet_id': self.subnet['id']}
        member_name = member_kwargs['address']

        first_member = self._create_member(first_pool['id'],
                                           **member_kwargs)

        # verify node
        node_exists = self.bigip.node_exists(member_name, self.parition)
        if not node_exists:
            self._delete_pool(first_pool['id'])
            assert node_exists


        # create second listener
        second_listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                                  'protocol': 'HTTPS',
                                  'protocol_port': 443}
        second_listener = self._create_listener(**second_listener_kwargs)
        self.addCleanup(self._delete_listener, second_listener['id'])

        # create second pool
        second_pool_kwargs = {'listener_id': second_listener['id'],
                              'protocol': 'HTTPS',
                              'lb_algorithm': 'ROUND_ROBIN'}
        second_pool = self._create_pool(**second_pool_kwargs)

        # create second member same as first
        second_member = self._create_member(second_pool['id'],
                                           **member_kwargs)

        # verify only have one node for two members
        nodes = self.bigip.get_nodes(partition=self.partition)
        if len(nodes) != 1:
            self._delete_pool(first_pool['id'])
            self._delete_pool(second_pool['id'])
            assert len(nodes == 1)

        # delete first pool/member
        self._delete_pool(first_pool['id'])

        # verify node still exists
        nodes = self.bigip.get_nodes(partition=self.partition)
        if len(nodes) != 1:
            self._delete_pool(second_pool['id'])
            assert len(nodes == 1)

        # delete second pool/member
        self._delete_pool(second_pool['id'])

        # verify no node
        nodes = self.bigip.get_nodes(partition=self.partition)
        assert len(nodes == 0)
