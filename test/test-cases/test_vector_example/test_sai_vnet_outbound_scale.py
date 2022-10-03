import json
from pathlib import Path
from pprint import pprint

import snappi
import time

import pytest
from saichallenger.dataplane.ptf_testutils import (send_packet,
                                                   simple_udp_packet,
                                                   simple_vxlan_packet,
                                                   verify_packet,
                                                   verify_no_other_packets)
import saichallenger.dataplane.snappi_trafic_utils as stu

current_file_dir = Path(__file__).parent

# Constants for scale outbound
NUMBER_OF_VIP = 2
NUMBER_OF_DLE = 2
NUMBER_OF_IN_ACL_GROUP = 10
NUMBER_OF_OUT_ACL_GROUP = 10
NUMBER_OF_VNET = 2
NUMBER_OF_ENI = 10
NUMBER_OF_EAM = NUMBER_OF_ENI * 2
NUMBER_OF_ORE = 5
NUMBER_OF_DST = 10
NUMBER_OF_OCPE = 1

TEST_VNET_OUTBOUND_CONFIG_SCALE = {

    'DASH_VIP': {
        'vpe': {
            'count': NUMBER_OF_VIP,
            'SWITCH_ID': '$SWITCH_ID',
            'IPV4': {
                'count': NUMBER_OF_VIP,
                'start': '172.16.1.100',
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
            'count': NUMBER_OF_IN_ACL_GROUP,
            'ADDR_FAMILY': 'IPv4'
        },
        'out_acl_group_id': {
            'count': NUMBER_OF_OUT_ACL_GROUP,
            'ADDR_FAMILY': 'IPv4'
        }
    },

    'DASH_VNET': {
        'vnet': {
            'count': NUMBER_OF_VNET,
            'VNI': {
                'count': NUMBER_OF_VNET,
                'start': 1000,
                'step': 1000
            }
        }
    },

    'DASH_ENI': {
        'eni': {
            'count': NUMBER_OF_ENI,
            'ACL_GROUP': {
                'INBOUND': {
                    'STAGE1': {
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE2': {
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE3': {
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE4': {
                        'list': 'DASH_ACL_GROUP#in_acl_group_id#0'
                    },
                    'STAGE5': {
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
                'start': '172.16.1.1',
                'step': '0.0.1.0'
            },
            'VM_VNI': {
                'count': NUMBER_OF_ENI,
                'start': 9
            },
            'VNET_ID': {
                'count': NUMBER_OF_ENI,
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
                'start': '00:CC:CC:CC:00:00'
            },
            'ENI_ID': {
                'count': NUMBER_OF_ENI,
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
                'start': 'DASH_ENI#eni#0',
                'delay': NUMBER_OF_DST
            },
            'DESTINATION': {
                'count': NUMBER_OF_DST,
                'start': '10.1.0.0/16',
                'step': '0.0.1.0'
            },
            'ACTION': 'ROUTE_VNET',
            'DST_VNET_ID': {
                'count': NUMBER_OF_VNET,
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
                'start': 'DASH_VNET#vnet#0'
            },
            'DIP': {
                'count': NUMBER_OF_OCPE,
                'start': '10.1.2.50',
                'step': '0.0.1.0'
            },
            'UNDERLAY_DIP': {
                'count': NUMBER_OF_OCPE,
                'start': '172.16.1.20',
                'step': '0.0.1.0'
            },
            'OVERLAY_DMAC': {
                'count': NUMBER_OF_OCPE,
                'start': '00:DD:DD:DD:00:00'
            },
            'USE_DST_VNET_VNI': True
        }
    }
}

class TestSaiVnetOutbound:

    # @pytest.mark.skip
    def test_create_vnet_config(self, confgen, dpu, dataplane):

        # confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG_SCALE)
        # confgen.generate()
        # for item in confgen.items():
        #     pprint(item)

        with (current_file_dir / 'test_vnet_outbound_setup_commands_scale.json').open(mode='r') as config_file:
            setup_commands = json.load(config_file)
        result = [*dpu.process_commands(setup_commands)]
        print("\n======= SAI commands RETURN values =======")
        # pprint(result)

    # @pytest.mark.skip
    def test_run_traffic_check(self, dpu, dataplane):
        dataplane.preapare_vxlan_packets(TEST_VNET_OUTBOUND_CONFIG_SCALE)

        dataplane.set_config()
        dataplane.start_traffic()

        stu.wait_for(lambda: dataplane.check_flows_all_packets_metrics(dataplane.flows, name="Custom flow group", show=True), "Test", timeout_seconds=10)

        print("Test passed !")

    # @pytest.mark.skip
    def test_remove_vnet_config(self, confgen, dpu, dataplane):

        # confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG_SCALE)
        # confgen.generate()

        # for item in confgen.items():
        #     item['OP'] = 'remove'
        #     pprint(item)

        with (current_file_dir / 'test_vnet_outbound_cleanup_commands_scale.json').open(mode='r') as config_file:
            cleanup_commands = json.load(config_file)

        result = [*dpu.process_commands(cleanup_commands)]
        print("\n======= SAI commands RETURN values =======")
        # pprint(result)
