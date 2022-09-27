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

TEST_VNET_OUTBOUND_CONFIG = {

    'ACL_TABLE_COUNT':                  1,
    'ENI_COUNT':                        1,
    'ENI_START':                        1,
    'IP_PER_ACL_RULE':                  1,
    'IP_MAPPED_PER_ACL_RULE':           1,
    'IP_ROUTE_DIVIDER_PER_ACL_RULE':    8,

    'DASH_VIP': [
        { 'vpe':
            { 'SWITCH_ID': '$SWITCH_ID',
              'IPv4': VIP }
        }
    ],

    'DASH_DIRECTION_LOOKUP': [
        { 'dle':
            { 'SWITCH_ID': '$SWITCH_ID',
              'VNI': OUTBOUND_VNI,
              'ACTION': 'SET_OUTBOUND_DIRECTION' }
        }
    ],

    'DASH_ACL_GROUP': [
        { 'in_acl_group_id':
            { 'ADDR_FAMILY': 'IPv4' }
        },
        { 'out_acl_group_id':
            { 'ADDR_FAMILY': 'IPv4' }
        }
    ],

    'DASH_VNET': [
        { 'vnet':
            { 'VNI': VNET_VNI }
        }
    ],

    'DASH_ENI': [
        { 'eni':
            {'ACL_GROUP': {
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
                            },
            'ADMIN_STATE': True,
            'CPS': 10000,
            'FLOWS': 10000,
            'PPS': 100000,
            'VM_UNDERLAY_DIP': SRC_VM_PA_IP,
            'VM_VNI': VM_VNI,
            'VNET_ID': '$vnet'}
        }
    ],

    'DASH_ENI_ETHER_ADDRESS_MAP': [
        { 'eam':
            { 'SWITCH_ID': '$SWITCH_ID',
              'MAC': ENI_MAC,
              'ENI_ID': '$eni' }
        }
    ],

    'DASH_OUTBOUND_ROUTING': [
        { 'ore':
            { 'SWITCH_ID': '$SWITCH_ID',
              'ENI_ID': '$eni',
              'DESTINATION': CA_PREFIX,
              'ACTION': 'ROUTE_VNET',
              'DST_VNET_ID': '$vnet' }
        }
    ],

    'DASH_OUTBOUND_CA_TO_PA': [
        { 'ocpe':
            { 'SWITCH_ID': '$SWITCH_ID',
              'DST_VNET_ID': '$vnet',
              'DIP': DST_PA_IP,
              'UNDERLAY_DIP': DST_PA_IP,
              'OVERLAY_DMAC': DST_CA_MAC,
              'USE_DST_VNET_VNI': True }
        }
    ]
}

# Constants for scale outbound
NUMBER_OF_VIP = 3
NUMBER_OF_DLE = 3
NUMBER_OF_IN_ACL_GROUP = 10
NUMBER_OF_OUT_ACL_GROUP = 10
NUMBER_OF_VNET = 50
NUMBER_OF_ENI = 10
NUMBER_OF_EAM = NUMBER_OF_ENI * 2
NUMBER_OF_ORE = 5
NUMBER_OF_DST = 10
NUMBER_OF_OCPE = 5

TEST_VNET_OUTBOUND_CONFIG_SCALE = {
    'DASH_VIP': {
        'vpe': {
            'count': NUMBER_OF_VIP,
            'SWITCH_ID': '$SWITCH_ID',
            'IPV4': {
                'count': NUMBER_OF_VIP,
                'type': 'IP',
                'start': '172.1.0.100',
                'step': '0.1.0.0'
            }
        }
    },
    'DASH_DIRECTION_LOOKUP': {
        'dle': {
            'count': NUMBER_OF_DLE,
            'SWITCH_ID': '$SWITCH_ID',
            'VNI': {
                'count': NUMBER_OF_DLE,
                'start': 100,
                'step': 100
            },
            'ACTION': 'SET_OUTBOUND_DIRECTION'
        }
    },
    'DASH_ACL_GROUP': {
        'in_acl_group_id': {
            'count': 'NUMBER_OF_IN_ACL_GROUP',
            'ADDR_FAMILY': 'IPv4'
        },
        'out_acl_group_id': {
            'count': 'NUMBER_OF_OUT_ACL_GROUP',
            'ADDR_FAMILY': 'IPv4'
        }
    },
    'DASH_VNET': {
        'vnet': {
            'count': NUMBER_OF_VNET,
            'VNI': {
                'count': NUMBER_OF_VNET,
                'start': 1000,
                'step': 10
            }
        }
    },
    'DASH_ENI': {
        'eni': {
            'count': NUMBER_OF_ENI,
            'ACL_GROUP': {
                'INBOUND': {
                    'STAGE1': {
                        'type': 'OID',
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE2': {
                        'type': 'OID',
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE3': {
                        'type': 'OID',
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE4': {
                        'type': 'OID',
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE5': {
                        'type': 'OID',
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    }
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
            'VM_UNDERLAY_DIP': {
                'count': NUMBER_OF_ENI,
                'type': 'IP',
                'start': '172.16.1.0',
                'step': '0.0.1.0'
            },
            'VM_VNI': {
                'count': NUMBER_OF_ENI,
                'start': 50
            },
            'VNET_ID': {
                'count': NUMBER_OF_ENI,
                'type': 'OID',
                'start': 'DASH_VNET#vnet#0'
            }
        }
    },
    'DASH_ENI_ETHER_ADDRESS_MAP': {
        'eam': {
            'count': NUMBER_OF_EAM,
            'SWITCH_ID': '$SWITCH_ID',
            'MAC': {
                'count': NUMBER_OF_EAM,
                'type': 'MAC',
                'start': '00:CC:CC:CC:00:00'
            },
            'ENI_ID': {
                'count': NUMBER_OF_ENI,
                'type': 'OID',
                'start': 'DASH_ENI#eni#0'
            }
        }
    },
    'DASH_OUTBOUND_ROUTING': {
        'ore': {
            'count': NUMBER_OF_ORE,
            'SWITCH_ID': '$SWITCH_ID',
            'ENI_ID': {
                'count': NUMBER_OF_ENI,
                'type': 'OID',
                'start': 'DASH_ENI#eni#0',
                'delay': NUMBER_OF_DST
            },
            'DESTINATION': {
                'count': NUMBER_OF_DST,
                'type': 'IP',
                'start': '10.1.0.0/24',
                'step': '0.0.1.0'
            },
            'ACTION': 'ROUTE_VNET',
            'DST_VNET_ID': {
                'count': NUMBER_OF_VNET,
                'type': 'OID',
                'start': 'DASH_VNET#vnet#0'
            }
        }
    },
    'DASH_OUTBOUND_CA_TO_PA': {
        'ocpe': {
            'count': NUMBER_OF_OCPE,
            'SWITCH_ID': '$SWITCH_ID',
            'DST_VNET_ID': {
                'count': NUMBER_OF_VNET,
                'type': 'OID',
                'start': 'DASH_VNET#vnet#0'
            },
            'DIP': {
                'count': NUMBER_OF_OCPE,
                'type': 'IP',
                'start': '10.1.2.50',
                'step': '0.0.1.0'
            },
            'UNDERLAY_DIP': {
                'count': NUMBER_OF_OCPE,
                'type': 'IP',
                'start': '172.16.1.20',
                'step': '0.0.1.0'
            },
            'OVERLAY_DMAC': {
                'count': NUMBER_OF_OCPE,
                'type': 'MAC',
                'start': '00:DD:DD:DD:00:00'
            },
            'USE_DST_VNET_VNI': True
        }
    }
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
