import json
from pathlib import Path
from pprint import pprint

import pytest
import saichallenger.dataplane.snappi.snappi_traffic_utils as stu
from saichallenger.dataplane.ptf_testutils import (send_packet,
                                                   simple_udp_packet,
                                                   simple_vxlan_packet,
                                                   verify_no_other_packets,
                                                   verify_packet)

import dash_helper.vnet2vnet_helper as dh

current_file_dir = Path(__file__).parent

# Constants
SWITCH_ID = 5

TEST_VNET_OUTBOUND_CONFIG = {

    "ENI_COUNT": 1,
    "ACL_RULES_NSG": 1,
    "ACL_TABLE_COUNT": 1,
    "IP_PER_ACL_RULE": 1,
    "IP_MAPPED_PER_ACL_RULE": 1,
    "IP_ROUTE_DIVIDER_PER_ACL_RULE": 1,

    'DASH_VIP': {
        'vpe': {
            'SWITCH_ID': '$SWITCH_ID',
            'IPV4': "172.16.1.100"
        }
    },

    'DASH_DIRECTION_LOOKUP': {
        'dle': {
            'SWITCH_ID': '$SWITCH_ID',
            'VNI': 100,
            'ACTION': 'SET_OUTBOUND_DIRECTION'
        }
    },

    'DASH_ACL_GROUP': {
        'in_acl_group_id': {
            'ADDR_FAMILY': 'IPv4'
        },
        'out_acl_group_id': {
            'ADDR_FAMILY': 'IPv4'
        }
    },

    'DASH_VNET': {
        'vnet': {
            'VNI': 1000
        }
    },

    'DASH_ENI': {
        'eni': {
            'ACL_GROUP': {
                'INBOUND': {
                    'STAGE1': '$in_acl_group_id_#{0}',
                    'STAGE2': '$in_acl_group_id_#{0}',
                    'STAGE3': '$in_acl_group_id_#{0}}',
                    'STAGE4': '$in_acl_group_id_#{0}}',
                    'STAGE5': '$in_acl_group_id_#{0}}'
                },
                'OUTBOUND': {
                    'STAGE1': 0,
                    'STAGE2': 0,
                    'STAGE3': 0,
                    'STAGE4': 0,
                    'STAGE5': 0
                }
            },
            'ADMIN_STATE': True,
            'CPS': 10000,
            'FLOWS': 10000,
            'PPS': 100000,
            'VM_UNDERLAY_DIP': "172.16.1.1",
            'VM_VNI': 9,
            'VNET_ID': '$vnet_#{0}'
        }
    },

    'DASH_ENI_ETHER_ADDRESS_MAP': {
        'eam': {
            'SWITCH_ID': '$SWITCH_ID',
            'MAC': "00:cc:cc:cc:00:00",
            'ENI_ID': '$eni_#{0}'
        }
    },

    'DASH_OUTBOUND_ROUTING': {
        'ore': {
            'SWITCH_ID': '$SWITCH_ID',
            'ENI_ID': '$eni_#{0}',
            'DESTINATION': "10.1.0.0/16",
            'ACTION': 'ROUTE_VNET',
            'DST_VNET_ID': '$vnet_#{0}'
        }
    },

    'DASH_OUTBOUND_CA_TO_PA': {
        'ocpe': {
            'SWITCH_ID': '$SWITCH_ID',
            'DST_VNET_ID': '$vnet_#{0}',
            'DIP': "10.1.2.50",
            'UNDERLAY_DIP': "172.16.1.20",
            'OVERLAY_DMAC': "00:DD:DD:DD:00:00",
            'USE_DST_VNET_VNI': True
        }
    }
}


class TestSaiVnetOutbound:

    def test_create_vnet_config(self, confgen, dpu, dataplane):

        # confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG)
        # confgen.generate()
        # results = []
        # for item in confgen.items():
        #     pprint(item)
        #     results.append(dpu.command_processor.process_command(item))

        with (current_file_dir / 'vnet_outbound_setup_commands_simple.json').open(mode='r') as config_file:
            setup_commands = json.load(config_file)
        result = [*dpu.process_commands(setup_commands)]
        print("\n======= SAI commands RETURN values =======")
        pprint(result)

    @pytest.mark.ptf
    def test_run_packets_check(self, dpu, dataplane):

        SRC_VM_IP = "10.1.1.10"
        OUTER_SMAC = "00:00:05:06:06:06"
        OUR_MAC = "00:00:02:03:04:05"

        VIP = TEST_VNET_OUTBOUND_CONFIG['DASH_VIP']['vpe']['IPV4']
        VNET_VNI = TEST_VNET_OUTBOUND_CONFIG['DASH_VNET']['vnet']['VNI']
        DIR_LOOKUP_VNI = TEST_VNET_OUTBOUND_CONFIG['DASH_DIRECTION_LOOKUP']['dle']['VNI']
        SRC_VM_PA_IP = TEST_VNET_OUTBOUND_CONFIG['DASH_ENI']['eni']['VM_UNDERLAY_DIP']
        ENI_MAC = TEST_VNET_OUTBOUND_CONFIG['DASH_ENI_ETHER_ADDRESS_MAP']['eam']['MAC']
        DST_CA_IP = TEST_VNET_OUTBOUND_CONFIG['DASH_OUTBOUND_CA_TO_PA']['ocpe']['DIP']
        DST_PA_IP = TEST_VNET_OUTBOUND_CONFIG['DASH_OUTBOUND_CA_TO_PA']['ocpe']["UNDERLAY_DIP"]
        DST_CA_MAC = TEST_VNET_OUTBOUND_CONFIG['DASH_OUTBOUND_CA_TO_PA']['ocpe']["OVERLAY_DMAC"]

        # # check VIP drop
        # WRONG_VIP = "172.16.100.100"
        # inner_pkt = simple_udp_packet(eth_dst="02:02:02:02:02:02",
        #                               eth_src=ENI_MAC,
        #                               ip_dst=DST_CA_IP,
        #                               ip_src=SRC_VM_IP)
        # vxlan_pkt = simple_vxlan_packet(eth_dst=OUR_MAC,
        #                                 eth_src=OUTER_SMAC,
        #                                 ip_dst=WRONG_VIP,
        #                                 ip_src=SRC_VM_PA_IP,
        #                                 udp_sport=11638,
        #                                 with_udp_chksum=False,
        #                                 vxlan_vni=OUTBOUND_VNI,
        #                                 inner_frame=inner_pkt)
        # print("\n\nSending packet with wrong vip...\n\n", vxlan_pkt.__repr__())
        # send_packet(dataplane, 0, vxlan_pkt)
        # print("\nVerifying drop...")
        # verify_no_other_packets(dataplane)

        # # check routing drop
        # WRONG_DST_CA = "10.200.2.50"
        # inner_pkt = simple_udp_packet(eth_dst="02:02:02:02:02:02",
        #                               eth_src=ENI_MAC,
        #                               ip_dst=WRONG_DST_CA,
        #                               ip_src=SRC_VM_IP)
        # vxlan_pkt = simple_vxlan_packet(eth_dst=OUR_MAC,
        #                                 eth_src=OUTER_SMAC,
        #                                 ip_dst=VIP,
        #                                 ip_src=SRC_VM_PA_IP,
        #                                 udp_sport=11638,
        #                                 with_udp_chksum=False,
        #                                 vxlan_vni=OUTBOUND_VNI,
        #                                 inner_frame=inner_pkt)
        # print("\nSending packet with wrong dst CA IP to verify routing drop...\n\n", vxlan_pkt.__repr__())
        # send_packet(dataplane, 0, vxlan_pkt)
        # print("\nVerifying drop...")
        # verify_no_other_packets(dataplane)

        # # check mapping drop
        # WRONG_DST_CA = "10.1.211.211"
        # inner_pkt = simple_udp_packet(eth_dst="02:02:02:02:02:02",
        #                               eth_src=ENI_MAC,
        #                               ip_dst=WRONG_DST_CA,
        #                               ip_src=SRC_VM_IP)
        # vxlan_pkt = simple_vxlan_packet(eth_dst=OUR_MAC,
        #                                 eth_src=OUTER_SMAC,
        #                                 ip_dst=VIP,
        #                                 ip_src=SRC_VM_PA_IP,
        #                                 udp_sport=11638,
        #                                 with_udp_chksum=False,
        #                                 vxlan_vni=OUTBOUND_VNI,
        #                                 inner_frame=inner_pkt)
        # print("\nSending packet with wrong dst CA IP to verify mapping drop...\n\n", vxlan_pkt.__repr__())
        # send_packet(dataplane, 0, vxlan_pkt)
        # print("\nVerifying drop...")
        # verify_no_other_packets(dataplane)

        # check forwarding
        inner_pkt = simple_udp_packet(eth_dst = "02:02:02:02:02:02",
                                      eth_src = ENI_MAC,
                                      ip_dst  = DST_CA_IP,
                                      ip_src  = SRC_VM_IP)
        vxlan_pkt = simple_vxlan_packet(eth_dst         = OUR_MAC,
                                        eth_src         = OUTER_SMAC,
                                        ip_dst          = VIP,
                                        ip_src          = SRC_VM_PA_IP,
                                        udp_sport       = 11638,
                                        with_udp_chksum = False,
                                        vxlan_vni       = DIR_LOOKUP_VNI,
                                        inner_frame     = inner_pkt)

        inner_exp_pkt = simple_udp_packet(eth_dst = DST_CA_MAC,
                                          eth_src = ENI_MAC,
                                          ip_dst  = DST_CA_IP,
                                          ip_src  = SRC_VM_IP)
        vxlan_exp_pkt = simple_vxlan_packet(eth_dst         = "00:00:00:00:00:00",
                                            eth_src         = "00:00:00:00:00:00",
                                            ip_dst          = DST_PA_IP,
                                            ip_src          = VIP,
                                            udp_sport       = 0, # TODO: Fix sport in pipeline
                                            with_udp_chksum = False,
                                            vxlan_vni       = VNET_VNI,
                                            vxlan_flags     = 0,
                                            inner_frame     = inner_exp_pkt)
        vxlan_exp_pkt['IP'].chksum = 0

        print("\nSending outbound packet...\n\n", vxlan_pkt.__repr__())
        send_packet(dataplane, 0, vxlan_pkt)
        print("\nVerifying packet...\n", vxlan_exp_pkt.__repr__())
        verify_packet(dataplane, vxlan_exp_pkt, 0)

    @pytest.mark.snappi
    def test_simple_vxlan_packet(self, dpu, dataplane):
        dh.scale_vnet_outbound_flows(dataplane, TEST_VNET_OUTBOUND_CONFIG)
        dataplane.set_config()
        dataplane.start_traffic()

        stu.wait_for(lambda: dh.check_flow_packets_metrics(dataplane, dataplane.flows[0], show=True)[0],
                    "Test", timeout_seconds=10)

    def test_remove_vnet_config(self, confgen, dpu, dataplane):

        # confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG)
        # confgen.generate()
        # results = []
        # for item in confgen.items():
        #     item['op'] = 'remove'
        #     pprint(item)
        #     results.append(dpu.command_processor.process_command(item))

        with (current_file_dir / 'vnet_outbound_setup_commands_simple.json').open(mode='r') as config_file:
            setup_commands = json.load(config_file)
        cleanup_commands = []
        for cmd in reversed(setup_commands):
            cleanup_commands.append({'name': cmd['name'], 'op': 'remove'})

        result = [*dpu.process_commands(cleanup_commands)]
        print("\n======= SAI commands RETURN values =======")
        pprint(result)
