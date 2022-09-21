import json
from pathlib import Path
from pprint import pprint

import pytest
from saichallenger.dataplane.ptf_testutils import (send_packet,
                                                   simple_udp_packet,
                                                   simple_vxlan_packet,
                                                   verify_packet,
                                                   verify_no_other_packets)

current_file_dir = Path(__file__).parent

# Constants
SWITCH_ID = 5
OUTBOUND_VNI = 60
VNET_VNI = 100
VM_VNI = 9
ENI_MAC = "00:cc:cc:cc:cc:cc"
OUR_MAC = "00:00:02:03:04:05"
DST_CA_MAC = "00:dd:dd:dd:dd:dd"
VIP = "172.16.1.100"
OUTBOUND_VNI = 100
DST_CA_IP = "10.1.2.50"
DST_PA_IP = "172.16.1.20"
SRC_VM_PA_IP = "172.16.1.1"
CA_PREFIX = "10.1.0.0/16"

# Constants for scale update
VIP_1 = "172.1.0.100"
VIP_2 = "172.2.0.100"
OUTBOUND_VNI_1 = 100
OUTBOUND_VNI_2 = 200
VNET_VNI_1 = 1000
VNET_VNI_2 = 2000
SRC_VM_PA_IP_1 = "172.1.0.1"
SRC_VM_PA_IP_2 = "172.2.0.1"
ENI_MAC_1 = "00:CC:CC:CC:CC:01"
ENI_MAC_2 = "00:CC:CC:CC:CC:02"
CA_PREFIX_1 = "10.0.1.0/24"
CA_PREFIX_2 = "10.0.2.0/24"
DST_PA_IP_1 = "10.0.1.10"
DST_PA_IP_2 = "10.0.2.10"
UNDERLAY_DIP_1 = "100.1.0.200"
UNDERLAY_DIP_2 = "100.2.0.200"
UNDERLAY_DIP_3 = "100.3.0.200"
UNDERLAY_DIP_4 = "100.4.0.200"
DST_CA_MAC_1 = "00:DD:DD:DD:DD:01"
DST_CA_MAC_2 = "00:DD:DD:DD:DD:02"
DST_CA_MAC_3 = "00:DD:DD:DD:DD:03"
DST_CA_MAC_4 = "00:DD:DD:DD:DD:04"

# Test Vector
TEST_VNET_OUTBOUND_CONFIG = {

    'ACL_TABLE_COUNT':                  1,
    'ENI_COUNT':                        1,
    'ENI_START':                        1,
    'IP_PER_ACL_RULE':                  1,
    'IP_MAPPED_PER_ACL_RULE':           1,
    'IP_ROUTE_DIVIDER_PER_ACL_RULE':    8,

    'DASH_VIP': [
        { 'vpe#1':
            { 'SWITCH_ID': '$SWITCH_ID',
              'IPv4': VIP_1 }
        },
        { 'vpe#2':
            { 'SWITCH_ID': '$SWITCH_ID',
              'IPv4': VIP_2 }
        }
    ],

    'DASH_DIRECTION_LOOKUP': [
        { 'dle#100':
            { 'SWITCH_ID': '$SWITCH_ID',
              'VNI': OUTBOUND_VNI_1,
              'ACTION': 'SET_OUTBOUND_DIRECTION' }
        },
        { 'dle#200':
            { 'SWITCH_ID': '$SWITCH_ID',
              'VNI': OUTBOUND_VNI_2,
              'ACTION': 'SET_OUTBOUND_DIRECTION' }
        }
    ],

    'DASH_VNET': [
        { 'vnet#1000':
            { 'VNI': VNET_VNI_1 }
        },
        { 'vnet#2000':
            { 'VNI': VNET_VNI_2 }
        }
    ],

    'DASH_ENI': [
        { 'eni#1':
            { 'CPS': 10000,
              'PPS': 100000,
              'FLOWS': 100000,
              'ADMIN_STATE': True,
              'VM_UNDERLAY_DIP': SRC_VM_PA_IP_1,
              'VM_VNI': VM_VNI,
              'VNET_ID': '$vnet#1000',
              'ACL_GROUP': {
                'INBOUND': [{ 'STAGE1': 0 },
                            { 'STAGE2': 0 },
                            { 'STAGE3': 0 },
                            { 'STAGE4': 0 },
                            { 'STAGE5': 0 }
                            ],
                'OUTBOUND': [{ 'STAGE1': 0 },
                             { 'STAGE2': 0 },
                             { 'STAGE3': 0 },
                             { 'STAGE4': 0 },
                             { 'STAGE5': 0 }
                             ]
                            } }
        },
        { 'eni#2':
            { 'CPS': 10000,
              'PPS': 100000,
              'FLOWS': 100000,
              'ADMIN_STATE': True,
              'VM_UNDERLAY_DIP': SRC_VM_PA_IP_2,
              'VM_VNI': VM_VNI,
              'VNET_ID': '$vnet#2000',
              'ACL_GROUP': {
                'INBOUND': [{ 'STAGE1': 0 },
                            { 'STAGE2': 0 },
                            { 'STAGE3': 0 },
                            { 'STAGE4': 0 },
                            { 'STAGE5': 0 }
                            ],
                'OUTBOUND': [{ 'STAGE1': 0 },
                             { 'STAGE2': 0 },
                             { 'STAGE3': 0 },
                             { 'STAGE4': 0 },
                             { 'STAGE5': 0 }
                             ]
                            } }
        }
    ],

    'DASH_ENI_ETHER_ADDRESS_MAP': [
        { 'eam#1':
            { 'SWITCH_ID': '$SWITCH_ID',
              'MAC': ENI_MAC_1,
              'ENI_ID': '$eni#1' }
        },
        { 'eam#2':
            { 'SWITCH_ID': '$SWITCH_ID',
              'MAC': ENI_MAC_2,
              'ENI_ID': '$eni#2' }
        }
    ],

    'DASH_OUTBOUND_ROUTING': [
        { 'ore#1':
            { 'SWITCH_ID': '$SWITCH_ID',
              'ENI_ID': '$eni#1',
              'DESTINATION': CA_PREFIX_1,
              'ACTION': 'ROUTE_VNET',
              'DST_VNET_ID': '$vnet#1000' }
        },
        { 'ore#2':
            { 'SWITCH_ID': '$SWITCH_ID',
              'ENI_ID': '$eni#1',
              'DESTINATION': CA_PREFIX_2,
              'ACTION': 'ROUTE_VNET',
              'DST_VNET_ID': '$vnet#2000' }
        },
        { 'ore#3':
            { 'SWITCH_ID': '$SWITCH_ID',
              'ENI_ID': '$eni#2',
              'DESTINATION': CA_PREFIX_1,
              'ACTION': 'ROUTE_VNET',
              'DST_VNET_ID': '$vnet#1000' }
        },
        { 'ore#4':
            { 'SWITCH_ID': '$SWITCH_ID',
              'ENI_ID': '$eni#2',
              'DESTINATION': CA_PREFIX_2,
              'ACTION': 'ROUTE_VNET',
              'DST_VNET_ID': '$vnet#2000' }
        }
    ],

    'DASH_OUTBOUND_CA_TO_PA': [
        { 'ocpe#1':
            { 'SWITCH_ID': '$SWITCH_ID',
              'DST_VNET_ID': '$vnet#1000',
              'DIP': DST_PA_IP_1,
              'UNDERLAY_DIP': UNDERLAY_DIP_1,
              'OVERLAY_DMAC': DST_CA_MAC_1,
              'USE_DST_VNET_VNI': True }
        },
        { 'ocpe#2':
            { 'SWITCH_ID': '$SWITCH_ID',
              'DST_VNET_ID': '$vnet#2000',
              'DIP': DST_PA_IP_1,
              'UNDERLAY_DIP': UNDERLAY_DIP_2,
              'OVERLAY_DMAC': DST_CA_MAC_2,
              'USE_DST_VNET_VNI': True }
        },
        { 'ocpe#3':
            { 'SWITCH_ID': '$SWITCH_ID',
              'DST_VNET_ID': '$vnet#1000',
              'DIP': DST_PA_IP_2,
              'UNDERLAY_DIP': UNDERLAY_DIP_3,
              'OVERLAY_DMAC': DST_CA_MAC_3,
              'USE_DST_VNET_VNI': True }
        },
        { 'ocpe#4':
            { 'SWITCH_ID': '$SWITCH_ID',
              'DST_VNET_ID': '$vnet#2000',
              'DIP': DST_PA_IP_2,
              'UNDERLAY_DIP': UNDERLAY_DIP_4,
              'OVERLAY_DMAC': DST_CA_MAC_4,
              'USE_DST_VNET_VNI': True }
        }
    ]
}


class TestSaiVnetOutbound:

    def test_create_vnet_config(self, confgen, dpu, dataplane):

        confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG)
        confgen.generate()
        for item in confgen.items():
            pprint(item)

        with (current_file_dir / 'test_vnet_outbound_setup_commands.json').open(mode='r') as config_file:
            setup_commands = json.load(config_file)
        result = [*dpu.process_commands(setup_commands)]
        print("\n======= SAI commands RETURN values =======")
        pprint(result)

    def test_run_traffic_check(self, dpu, dataplane):

        SRC_VM_IP = "10.1.1.10"
        OUTER_SMAC = "00:00:05:06:06:06"
        INNER_SMAC = "00:00:04:06:06:06"

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
                                        vxlan_vni       = OUTBOUND_VNI,
                                        inner_frame     = inner_pkt)

        inner_exp_pkt = simple_udp_packet(eth_dst=DST_CA_MAC,
                                      eth_src=ENI_MAC,
                                      ip_dst=DST_CA_IP,
                                      ip_src=SRC_VM_IP)
        vxlan_exp_pkt = simple_vxlan_packet(eth_dst="00:00:00:00:00:00",
                                        eth_src="00:00:00:00:00:00",
                                        ip_dst=DST_PA_IP,
                                        ip_src=VIP,
                                        udp_sport=0, # TODO: Fix sport in pipeline
                                        with_udp_chksum=False,
                                        vxlan_vni=VNET_VNI,
                                        vxlan_flags=0,
                                        inner_frame=inner_exp_pkt)
        vxlan_exp_pkt['IP'].chksum = 0

        self.pkt_exp = vxlan_exp_pkt
        print("\nSending outbound packet...\n\n", vxlan_pkt.__repr__())
        send_packet(dataplane, 0, vxlan_pkt)
        print("\nVerifying packet...\n", vxlan_exp_pkt.__repr__())
        verify_packet(dataplane, vxlan_exp_pkt, 0)
        print ("test_sai_thrift_outbound_udp_pkt_test OK")

    def test_remove_vnet_config(self, confgen, dpu, dataplane):

        confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG)
        confgen.generate()

        for item in confgen.items():
            item['OP'] = 'remove'
            pprint(item)

        with (current_file_dir / 'test_vnet_outbound_cleanup_commands.json').open(mode='r') as config_file:
            cleanup_commands = json.load(config_file)

        result = [*dpu.process_commands(cleanup_commands)]
        print("\n======= SAI commands RETURN values =======")
        pprint(result)
