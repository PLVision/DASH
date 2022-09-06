import logging
from pathlib import Path

current_file_dir = Path(__file__).parent


def exec_commands(dpu, commands):
    commands_gen = iter(commands)
    results_gen = dpu.process_commands(commands)
    while True:
        try:
            command = next(commands_gen)
        except StopIteration:
            break
        try:
            result = next(results_gen)
        except Exception as e:
            raise AssertionError(f"Unable execute command {command}") from e
        else:
            logging.info(f'Command {command} succeed with result {result}')


def test_vnet_outbound(dpu, dataplane):
    vip = "172.16.1.100"
    vnet_vni = 100
    outbound_vni = 100
    src_vm_pa_ip = "172.16.1.1"
    eni_mac = "00:cc:cc:cc:cc:cc"
    dst_ca_mac = "00:dd:dd:dd:dd:dd"
    dst_ca_ip = "10.1.2.50"
    dst_pa_ip = "172.16.1.20"

    vnet_outbound_setup_commands = [
        dict(
            name="vip_entry",
            op="create",
            type="SAI_OBJECT_TYPE_VIP_ENTRY",
            key=dict(switch_id="$SWITCH_ID", vip=vip),
            attributes=[
                *("SAI_VIP_ENTRY_ATTR_ACTION", "SAI_VIP_ENTRY_ACTION_ACCEPT")
            ]
        ),
        dict(
            name="direction_lookup_entry",
            op="create",
            type="SAI_OBJECT_TYPE_DIRECTION_LOOKUP_ENTRY",
            key=dict(switch_id="$SWITCH_ID", vni=outbound_vni),
            attributes=[
                *("SAI_DIRECTION_LOOKUP_ENTRY_ATTR_ACTION", "SAI_DIRECTION_LOOKUP_ENTRY_ACTION_SET_OUTBOUND_DIRECTION")
            ]
        ),
        dict(
            name="acl_in_1",
            op="create",
            type="SAI_OBJECT_TYPE_DASH_ACL_GROUP",
            attributes=[
                *("SAI_DASH_ACL_GROUP_ATTR_IP_ADDR_FAMILY", "SAI_IP_ADDR_FAMILY_IPV4")
            ]
        ),
        dict(
            name="acl_out_1",
            op="create",
            type="SAI_OBJECT_TYPE_DASH_ACL_GROUP",
            attributes=[*("SAI_DASH_ACL_GROUP_ATTR_IP_ADDR_FAMILY", "SAI_IP_ADDR_FAMILY_IPV4")
            ]
        ),
        dict(
            name="vnet_1",
            op="create",
            type="SAI_OBJECT_TYPE_VNET",
            attributes=[
                *("SAI_VNET_ATTR_VNI", vnet_vni)
            ]
        ),
        dict(
            name="eni_id",
            op="create",
            type="SAI_OBJECT_TYPE_ENI",
            attributes=[
                *("SAI_ENI_ATTR_CPS", "10000"),
                *("SAI_ENI_ATTR_PPS", "100000"),
                *("SAI_ENI_ATTR_FLOWS", "100000"),
                *("SAI_ENI_ATTR_ADMIN_STATE", "True"),
                *("SAI_ENI_ATTR_VM_UNDERLAY_DIP", src_vm_pa_ip),
                *("SAI_ENI_ATTR_VM_VNI", "9"),
                *("SAI_ENI_ATTR_VNET_ID", "$vnet_1"),
                *("SAI_ENI_ATTR_INBOUND_V4_STAGE1_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V4_STAGE2_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V4_STAGE3_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V4_STAGE4_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V4_STAGE5_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V6_STAGE1_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V6_STAGE2_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V6_STAGE3_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V6_STAGE4_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_INBOUND_V6_STAGE5_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V4_STAGE1_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V4_STAGE2_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V4_STAGE3_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V4_STAGE4_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V4_STAGE5_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V6_STAGE1_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V6_STAGE2_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V6_STAGE3_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V6_STAGE4_DASH_ACL_GROUP_ID", "0"),
                *("SAI_ENI_ATTR_OUTBOUND_V6_STAGE5_DASH_ACL_GROUP_ID", "0"),
            ]
        ),
        dict(
            name="eni_ether_address_map_entry",
            op="create",
            type="SAI_OBJECT_TYPE_ENI_ETHER_ADDRESS_MAP_ENTRY",
            key=dict(
                switch_id="$SWITCH_ID",
                address=eni_mac
            ),
            attributes=[
                *("SAI_ENI_ETHER_ADDRESS_MAP_ENTRY_ATTR_ENI_ID", "$eni_id")
            ]
        ),
        dict(
            name="outbound_routing_entry",
            op="create",
            type="SAI_OBJECT_TYPE_OUTBOUND_ROUTING_ENTRY",
            key=dict(
                switch_id="$SWITCH_ID",
                eni_id="$eni_id",
                destination="10.1.0.0/16"
            ),
            attributes=[
                *("SAI_OUTBOUND_ROUTING_ENTRY_ATTR_ACTION", "SAI_OUTBOUND_ROUTING_ENTRY_ACTION_ROUTE_VNET"),
                *("SAI_OUTBOUND_ROUTING_ENTRY_ATTR_DST_VNET_ID", "$vnet_1")
            ]
        ),
        dict(
            name="outbound_ca_to_pa_entry",
            op="create",
            type="SAI_OBJECT_TYPE_OUTBOUND_CA_TO_PA_ENTRY",
            key=dict(
                switch_id="$SWITCH_ID",
                dip=dst_ca_ip,
                dst_vnet_id="$vnet_1"
            ),
            attributes=[
                *("SAI_OUTBOUND_CA_TO_PA_ENTRY_ATTR_UNDERLAY_DIP", dst_pa_ip),
                *("SAI_OUTBOUND_CA_TO_PA_ENTRY_ATTR_OVERLAY_DMAC", dst_ca_mac),
                *("SAI_OUTBOUND_CA_TO_PA_ENTRY_ATTR_USE_DST_VNET_VNI", "true")
            ]
        )
    ]

    exec_commands(dpu, vnet_outbound_setup_commands)

    vnet_outbound_cleanup_commands = [
        dict(name="outbound_ca_to_pa_entry", op='remove'),
        dict(name="outbound_routing_entry", op='remove'),
        dict(name="eni_ether_address_map_entry", op='remove'),
        dict(name="eni_id", op='remove'),
        dict(name="vnet_1", op='remove'),
        dict(name="acl_out_1", op='remove'),
        dict(name="acl_in_1", op='remove'),
        dict(name="direction_lookup_entry", op='remove'),
        dict(name="vip_entry", op='remove'),
    ]

    exec_commands(dpu, vnet_outbound_cleanup_commands)
