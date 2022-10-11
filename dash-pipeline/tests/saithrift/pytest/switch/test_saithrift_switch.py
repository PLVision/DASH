import pytest

from sai_thrift.sai_headers import *
from sai_thrift.sai_adapter import *
from sai_thrift.ttypes  import *
       
@pytest.mark.saithrift
@pytest.mark.bmv2
@pytest.mark.switch
def test_sai_thrift_get_switch_attributes(saithrift_client):
    attr = sai_thrift_get_switch_attribute(
        saithrift_client, number_of_active_ports=True)
    number_of_active_ports = attr['number_of_active_ports']

    print ("number_of_active_ports = %d" % number_of_active_ports)
    assert(number_of_active_ports != 0)

    attr = sai_thrift_get_switch_attribute(
        saithrift_client,
        port_list=sai_thrift_object_list_t(idlist=[], count=int(number_of_active_ports)))
    assert(number_of_active_ports == attr['port_list'].count)
    port_list = attr['port_list'].idlist
    print ("port list = ", port_list)

    attr = sai_thrift_get_switch_attribute(
        saithrift_client, default_vlan_id=True)
    default_vlan_id = attr['default_vlan_id']
    print ("default_vlan_id = %d" % default_vlan_id)
    assert(default_vlan_id != 0)

    attr = sai_thrift_get_switch_attribute(
        saithrift_client, default_virtual_router_id=True)
    default_virtual_router_id = attr['default_virtual_router_id']
    print ("default_virtual_router_id = %d" % default_virtual_router_id)
    assert(default_virtual_router_id != 0)
    
    print ("test_sai_thrift_get_switch_attribute OK")