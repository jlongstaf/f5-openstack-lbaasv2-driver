# coding=utf-8
u"""F5 Networks® LBaaSv2 L7 policy rules tempest tests."""
# Copyright 2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import time

from tempest import config
from tempest.lib import exceptions
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.services.clients.bigip_client import \
    BigIpClient
from f5lbaasdriver.test.tempest.tests.api import base


CONF = config.CONF


class ListenerTestJSON(base.BaseTestCase):
    """Listener tempest tests.

    Tests the following operations in the Neutron-LBaaS API using the
    REST client with default credentials:
    """

    @classmethod
    def resource_setup(cls):
        super(ListenerTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('lbaasv2', 'network'):
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

        cls.partition = 'Project_' + cls.subnet['tenant_id']

        # create BigIp client for validating BIG-IP configuration
        cls.bigip = BigIpClient()

        # get an RPC client for checking driver service object
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @classmethod
    def resource_cleanup(cls):
        super(ListenerTestJSON, cls).resource_cleanup()

    def wait_for_active(self, obj_type, id):
        interval_time = 1
        timeout = 10
        end_time = time.time() + timeout
        status = "??"
        while time.time() < end_time:
            # get service object from driver
            res = self.client.call(self.context,
                                   "get_service_by_loadbalancer_id",
                                   loadbalancer_id=self.load_balancer_id)

            for obj in res[obj_type]:
                if (obj['id'] == id):
                    status = obj['provisioning_status']
                    if status == 'ACTIVE':
                        return
                    break
            time.sleep(interval_time)


        raise exceptions.TimeoutException(
            "Instance of {0} failed to go ACTIVE. Status is {1}".format(
                obj_type, status))

    @test.attr(type='smoke')
    def test_create_tcp_listener(self):
        # Create listener
        listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                           'protocol': 'TCP',
                           'protocol_port': '44'}
        listener = (self._create_listener(**listener_kwargs))
        self.addCleanup(self._delete_listener, listener['id'])

        # expect listener to go 'ACTIVE'
        self.wait_for_active('listeners', listener['id'])

        # check vs created
        vs_name = 'Project_' + str(listener['id'])
        assert self.bigip.virtual_server_exists(vs_name, self.partition)

        # check profiles
        assert self.bigip.virtual_server_has_profile(
            vs_name, 'fastL4', self.partition)

        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'http', self.partition)

        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'oneconnect', self.partition)

    @test.attr(type='smoke')
    def test_create_http_listener(self):
        # Create listener
        listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                           'protocol': 'HTTP',
                           'protocol_port': '80'}
        listener = (self._create_listener(**listener_kwargs))
        self.addCleanup(self._delete_listener, listener['id'])

        # expect listener to go 'ACTIVE'
        self.wait_for_active('listeners', listener['id'])

        # check vs created
        vs_name = 'Project_' + str(listener['id'])
        assert self.bigip.virtual_server_exists(vs_name, self.partition)

        # check profiles
        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'fastL4', self.partition)

        assert self.bigip.virtual_server_has_profile(
            vs_name, 'http', self.partition)

        assert self.bigip.virtual_server_has_profile(
            vs_name, 'oneconnect', self.partition)

    @test.attr(type='smoke')
    def test_create_https_listener(self):
        # Create listener
        listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                           'protocol': 'HTTPS',
                           'protocol_port': '443'}
        listener = (self._create_listener(**listener_kwargs))
        self.addCleanup(self._delete_listener, listener['id'])

        # expect listener to go 'ACTIVE'
        self.wait_for_active('listeners', listener['id'])

        # check vs created
        vs_name = 'Project_' + str(listener['id'])
        assert self.bigip.virtual_server_exists(vs_name, self.partition)

        # check profiles
        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'fastL4', self.partition)

        assert self.bigip.virtual_server_has_profile(
            vs_name, 'http', self.partition)

        assert self.bigip.virtual_server_has_profile(
            vs_name, 'oneconnect', self.partition)

    @test.attr(type='smoke')
    def test_tcp_session_persistence(self):
        # Create listener
        listener_kwargs = {'loadbalancer_id': self.load_balancer_id,
                           'protocol': 'TCP',
                           'protocol_port': '8443'}
        listener = self._create_listener(**listener_kwargs)
        self.addCleanup(self._delete_listener, listener['id'])

        # expect listener to go 'ACTIVE'
        self.wait_for_active('listeners', listener['id'])

        # check vs created
        vs_name = 'Project_' + str(listener['id'])
        assert self.bigip.virtual_server_exists(vs_name, self.partition)

        # check profiles
        assert self.bigip.virtual_server_has_profile(
            vs_name, 'fastL4', self.partition)

        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'http', self.partition)

        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'oneconnect', self.partition)

        # attach pool with session persistence
        pool_kwargs = {'listener_id': listener['id'],
                       'protocol': 'TCP',
                       'lb_algorithm': 'ROUND_ROBIN',
                       'session_persistence': {'type': 'HTTP_COOKIE'}}
        pool = self._create_pool(**pool_kwargs)
        self.addCleanup(self._delete_pool, pool['id'])
        self.wait_for_active('pools', pool['id'])

        # still expect fastl4
        assert self.bigip.virtual_server_has_profile(
            vs_name, 'fastL4', self.partition)

        # now expect http profile was added
        assert self.bigip.virtual_server_has_profile(
            vs_name, 'http', self.partition)

        # still do not expect oneconnect
        assert not self.bigip.virtual_server_has_profile(
            vs_name, 'oneconnect', self.partition)
