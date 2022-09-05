from pprint import pprint
import pytest
from saichallenger.dataplane.ptf_testutils import send_packet, verify_packet, simple_udp_packet, simple_vxlan_packet


# Constants
VIP = "10.10.1.1"
SWITCH_ID = 1
DIR_LOOKUP_VNI = 60
VM_VNI = 9
ENI_MAC = "00:00:00:09:03:14"
PA_VALIDATION_SIP = "10.10.2.10"
PA_VALIDATION_DIP = "10.10.2.20"
INBOUND_ROUTING_VNI = 2
INNER_VM_IP = "172.19.1.100"
INNER_REMOTE_IP = "172.19.1.1"

# Test Vector
TEST_VNET_INBOUND_CONFIG = {

    'ENI_COUNT': 2,

    'DASH_VIP': [
        {'vip_1': {'IPv4': VIP}}
    ],

    'DASH_DIRECTION_LOOKUP': [
        {'direction_lookup': {'VNI': DIR_LOOKUP_VNI}}
    ],

    'DASH_ACL_GROUP': [
        {'acl_out_1': {'ADDR_FAMILY': 'IPv4"'}}
    ],

    'DASH_ACL_RULE': [
        {'acl_rule_1': {'action': 'permit"',
                        'dip': '10.0.0.1',
                        'gid': '$acl_out_1',
                        'priority': 10}
        }
    ],

    'DASH_VNET': [
        {'vnet_1': {'VNI': DIR_LOOKUP_VNI}}
    ],

    'DASH_ENI': [
        {'eni_1':
            {'ACL_GROUP': {
                'INBOUND': [{'STAGE1': '$acl_in_1'},
                            {'STAGE2': '$acl_in_1'},
                            {'STAGE3': '$acl_in_1'},
                            {'STAGE4': '$acl_in_1'},
                            {'STAGE5': '$acl_in_1'}
                            ],
                'OUTBOUND': [{'STAGE1': '$acl_out_1'},
                             {'STAGE2': '$acl_out_1'},
                             {'STAGE3': '$acl_out_1'},
                             {'STAGE4': '$acl_out_1'},
                             {'STAGE5': '$acl_out_1'}
                             ]
                            },
            'ADMIN_STATE': True,
            'CPS': 10000,
            'FLOWS': 10000,
            'PPS': 100000,
            'VM_UNDERLAY_DIP': PA_VALIDATION_DIP,
            'VM_VNI': VM_VNI,
            'VNET_ID': '$vnet_1'}
        }
    ],

    'DASH_ENI_ETHER_ADDRESS_MAP': [
        {'address_map_1': {
            'MAC': ENI_MAC,
            'VNI': INBOUND_ROUTING_VNI}
        }
    ],

    'DASH_ROUTE_RULE_TABLE': [
        {'inbound_routing_1': {
            'VNI': INBOUND_ROUTING_VNI,
            'action_type': 'DECAP_PA_VALIDATE'}
        }
    ],

    'DASH_PA_VALIDATION': [
        {'pa_validation_1': {'action': 'permit',
                             'eni': '$eni_1',
                             'sip': PA_VALIDATION_SIP,
                             'switch_id': SWITCH_ID,
                             'vni': INBOUND_ROUTING_VNI}
        }
    ]

}


class TestSaiVnetInbound:

    def test_create_vnet_config(self, confgen, dpu, dataplane):

        confgen.mergeParams(TEST_VNET_INBOUND_CONFIG)
        confgen.generate()

        for item in confgen.items():
            # dpu.process_commands(item)
            # dpu.process_commands(confgen.items())
            pprint(item)

    def test_run_traffic_check(self, dpu, dataplane):
        # Check forwarding

        outer_smac = "00:0a:05:06:06:06"
        outer_dmac = "00:0b:05:06:06:06"
        inner_smac = "00:0a:04:06:06:06"
        inner_dmac = "00:0b:04:06:06:06"

        # PAcket to send
        inner_pkt = simple_udp_packet(eth_dst=ENI_MAC,
                                        eth_src=inner_smac,
                                        ip_dst=INNER_VM_IP,
                                        ip_src=INNER_REMOTE_IP)
        vxlan_pkt = simple_vxlan_packet(eth_dst=outer_dmac,
                                        eth_src=outer_smac,
                                        ip_dst=PA_VALIDATION_DIP,
                                        ip_src=PA_VALIDATION_SIP,
                                        udp_sport=11638,
                                        with_udp_chksum=False,
                                        vxlan_vni=DIR_LOOKUP_VNI,
                                        inner_frame=inner_pkt)

        # Expected Packet to check
        inner_exp_pkt = simple_udp_packet(eth_dst=inner_dmac,
                                            eth_src=ENI_MAC,
                                            ip_dst=INNER_VM_IP,
                                            ip_src=INNER_REMOTE_IP)
        vxlan_exp_pkt = simple_vxlan_packet(eth_dst="00:00:00:00:00:00",
                                        eth_src="00:00:00:00:00:00",
                                        ip_dst=PA_VALIDATION_DIP,
                                        ip_src=PA_VALIDATION_SIP,
                                        udp_sport=0,
                                        with_udp_chksum=False,
                                        vxlan_vni=INBOUND_ROUTING_VNI,
                                        inner_frame=inner_exp_pkt)
        # TODO: Fix IP chksum
        # vxlan_exp_pkt[IP].chksum = 0
        # # TODO: Fix UDP length
        # vxlan_exp_pkt[IP][UDP][VXLAN].flags = 0

        print("\nSending outbound packet...\n\n", vxlan_pkt.__repr__())
        # send_packet(dataplane, 0, vxlan_pkt)

        print("\nVerifying packet...\n", vxlan_exp_pkt.__repr__())
        # verify_packet(dataplane, vxlan_exp_pkt, 1)

        print ("run_traffic_check OK")

        pytest.set_trace()

    def test_remove_vnet_config(self, confgen, dpu, dataplane):

        confgen.mergeParams(TEST_VNET_INBOUND_CONFIG)
        confgen.generate()

        for item in confgen.items():
            item['OP'] = 'remove'
            pprint(item)
            #dpu.process_commands(item)
