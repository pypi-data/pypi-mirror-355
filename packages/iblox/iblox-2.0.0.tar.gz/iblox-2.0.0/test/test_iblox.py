#!/usr/bin/env python
# coding=utf-8
"""Integration and unit Tests for iblox Python Module"""
from __future__ import print_function
import requests_mock
import unittest
import warnings
from builtins import str


__author__ = 'Jesse Almanrode'

import iblox

class TestIPv4AddrObj(unittest.TestCase):
    def test_basic(self):
        result = iblox.ipv4addr_obj("192.168.1.1")
        self.assertEqual(result, {"configure_for_dhcp": False, "ipv4addr": "192.168.1.1"})

    def test_with_kwargs(self):
        result = iblox.ipv4addr_obj("10.0.0.1", foo="bar", number=42)
        self.assertEqual(result["ipv4addr"], "10.0.0.1")
        self.assertEqual(result["foo"], "bar")
        self.assertEqual(result["number"], 42)
        self.assertFalse(result["configure_for_dhcp"])

    def test_override_configure_for_dhcp(self):
        result = iblox.ipv4addr_obj("8.8.8.8", configure_for_dhcp=True)
        self.assertTrue(result["configure_for_dhcp"])
        self.assertEqual(result["ipv4addr"], "8.8.8.8")

    def test_ipaddr_types(self):
        # Accepts any type, just assigns to dict
        self.assertEqual(iblox.ipv4addr_obj(1234)["ipv4addr"], 1234)
        self.assertEqual(iblox.ipv4addr_obj(None)["ipv4addr"], None)

    def test_missing_ipaddr(self):
        with self.assertRaises(TypeError):
            iblox.ipv4addr_obj()


@requests_mock.Mocker()
class Testiblox(unittest.TestCase):

    def setUp(self):
        """ Even though this looks like a real connection, it isn't
        """
        self.iblox_conn = iblox.Infoblox('https://localhost/wapi/v2.3.1', username='admin', password='infoblox')

    def test_verify(self, mock_adapter):
        """ Test Infoblox.verify method
        """
        result = self.iblox_conn.verify(objtype='host', name_regex='test.*', _return_type='json')
        self.assertTrue(isinstance(result, dict))
        self.assertIn('name~', result.keys())
        pass

    def test_get(self, mock_adapter):
        """ Test Infoblox.get method
        """
        mock_adapter.get(requests_mock.ANY, json=[{'_ref': 'view/ZG5zLnZpZXckLl9kZWZhdWx0:default/true', 'is_default': True, 'name': 'default'}])
        result = self.iblox_conn.get(objtype='view', name='default')
        self.assertTrue(isinstance(result, list))
        self.assertEqual(len(result), 1)
        self.assertTrue(isinstance(result[0], dict))
        self.assertEqual(result[0]['_ref'], 'view/ZG5zLnZpZXckLl9kZWZhdWx0:default/true')
        pass

    def test_add(self, mock_adapter):
        """ Test Infoblox.add method
        """
        mock_adapter.post(requests_mock.ANY, json='zone_auth/ZG5zLnpvbmUkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3Q:unittest.example/default')
        result = self.iblox_conn.add(objtype='zone_auth', fqdn='unittest.example')
        self.assertTrue(isinstance(result, str))
        self.assertEqual(result, 'zone_auth/ZG5zLnpvbmUkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3Q:unittest.example/default')
        pass

    def test_add_host(self, mock_adapter):
        """ Test Infoblox.add_host method
        """
        mock_adapter.post(requests_mock.ANY, json='record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        result = self.iblox_conn.add_host('testhost.unittest.example', '192.168.2.8', comment='Created by test_infoblox.py')
        self.assertTrue(isinstance(result, str))
        self.assertEqual(result, 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        pass

    def test_add_alias(self, mock_adapter):
        """ Test Infoblox.add_alias method
        """
        mock_adapter.get(requests_mock.ANY, json=[{'_ref': 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default', 'ipv4addrs': [{'_ref': 'record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuZXhhbXBsZS51bml0dGVzdC50ZXN0aG9zdC4xOTIuMTY4LjIuOC4:192.168.2.8/testhost.unittest.example/default', 'configure_for_dhcp': False, 'host': 'testhost.unittest.example', 'ipv4addr': '192.168.2.8'}], 'name': 'testhost.unittest.example', 'view': 'default'}])
        mock_adapter.put(requests_mock.ANY, json='record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        result = self.iblox_conn.add_alias('testhost.unittest.example', 'testalias.unittest.example')
        self.assertTrue(isinstance(result, str))
        self.assertEqual(result, 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        pass

    def test_delete_alias(self, mock_adapter):
        """ Test Infoblox.delete_alias method
        """
        mock_adapter.get(requests_mock.ANY, json=[{'_ref': 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default', 'ipv4addrs': [{'_ref': 'record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuZXhhbXBsZS51bml0dGVzdC50ZXN0aG9zdC4xOTIuMTY4LjIuOC4:192.168.2.8/testhost.unittest.example/default', 'configure_for_dhcp': False, 'host': 'testhost.unittest.example', 'ipv4addr': '192.168.2.8'}], 'name': 'testhost.unittest.example', 'view': 'default'}])
        mock_adapter.delete(requests_mock.ANY, json='record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        result = self.iblox_conn.delete_alias('testhost.unittest.example', 'testalias.unittest.example')
        self.assertTrue(isinstance(result, dict))
        self.assertEqual(result['_ref'], 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        pass

    def test_delete_host(self, mock_adapter):
        """ Test Infoblox.delete_host method
        """
        mock_adapter.get(requests_mock.ANY, json=[{'_ref': 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default', 'ipv4addrs': [{'_ref': 'record:host_ipv4addr/ZG5zLmhvc3RfYWRkcmVzcyQuX2RlZmF1bHQuZXhhbXBsZS51bml0dGVzdC50ZXN0aG9zdC4xOTIuMTY4LjIuOC4:192.168.2.8/testhost.unittest.example/default', 'configure_for_dhcp': False, 'host': 'testhost.unittest.example', 'ipv4addr': '192.168.2.8'}], 'name': 'testhost.unittest.example', 'view': 'default'}])
        mock_adapter.delete(requests_mock.ANY, json='record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        result = self.iblox_conn.get_host_by_name('testhost.unittest.example')[0]
        result = self.iblox_conn.delete(result['_ref'])
        self.assertTrue(isinstance(result, str))
        self.assertEqual(result, 'record:host/ZG5zLmhvc3QkLl9kZWZhdWx0LmV4YW1wbGUudW5pdHRlc3QudGVzdGhvc3Q:testhost.unittest.example/default')
        pass


if __name__ == '__main__':
    with warnings.catch_warnings(record=True):
        unittest.main(failfast=True)
