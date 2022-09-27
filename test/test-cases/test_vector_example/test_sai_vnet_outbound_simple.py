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

    'DASH_VIP': {
        'vpe': {
            'SWITCH_ID': '$SWITCH_ID',
            'IPV4': {
                'type': 'IP',
                'start': VIP
            }
        }
    },

    'DASH_DIRECTION_LOOKUP': {
        'dle': {
            'SWITCH_ID': '$SWITCH_ID',
            'VNI': {
                'start': OUTBOUND_VNI
            },
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
            'VNI': {
                'start': VNET_VNI
            }
        }
    },

    'DASH_ENI': {
        'eni': {
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
                'type': 'IP',
                'start': SRC_VM_PA_IP
            },
            'VM_VNI': {
                'start': VM_VNI
            },
            'VNET_ID': {
                'type': 'OID',
                'start': 'DASH_VNET#vnet#0'
            }
        }
    },

    'DASH_ENI_ETHER_ADDRESS_MAP': {
        'eam': {
            'SWITCH_ID': '$SWITCH_ID',
            'MAC': {
                'type': 'MAC',
                'start': ENI_MAC
            },
            'ENI_ID': {
                'type': 'OID',
                'start': 'DASH_ENI#eni#0'
            }
        }
    },

    'DASH_OUTBOUND_ROUTING': {
        'ore': {
            'SWITCH_ID': '$SWITCH_ID',
            'ENI_ID': {
                'type': 'OID',
                'start': 'DASH_ENI#eni#0',
            },
            'DESTINATION': {
                'type': 'IP',
                'start': CA_PREFIX
            },
            'ACTION': 'ROUTE_VNET',
            'DST_VNET_ID': {
                'type': 'OID',
                'start': 'DASH_VNET#vnet#0'
            }
        }
    },

    'DASH_OUTBOUND_CA_TO_PA': {
        'ocpe': {
            'SWITCH_ID': '$SWITCH_ID',
            'DST_VNET_ID': {
                'type': 'OID',
                'start': 'DASH_VNET#vnet#0'
            },
            'DIP': {
                'type': 'IP',
                'start': DST_PA_IP
            },
            'UNDERLAY_DIP': {
                'type': 'IP',
                'start': DST_PA_IP
            },
            'OVERLAY_DMAC': {
                'type': 'MAC',
                'start': DST_CA_MAC
            },
            'USE_DST_VNET_VNI': True
        }
    }
}

class TestSaiVnetOutbound:

    # @pytest.mark.skip
    def test_create_vnet_config(self, confgen, dpu, dataplane):

        confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG)
        confgen.generate()
        for item in confgen.items():
            pprint(item)

        with (current_file_dir / 'test_vnet_outbound_setup_commands_simple.json').open(mode='r') as config_file:
            setup_commands = json.load(config_file)
        result = [*dpu.process_commands(setup_commands)]
        print("\n======= SAI commands RETURN values =======")
        pprint(result)

    def test_simple_vxlan_packet(self, dpu, dataplane):
        flow = dataplane.add_flow(name = "flow p1 > p2")
        api = dataplane.api
        cfg = dataplane.configuration

        SRC_VM_IP = "10.1.1.10"
        OUTER_SMAC = "00:00:05:06:06:06"
        INNER_SMAC = "00:00:04:06:06:06"

        dataplane.add_simple_vxlan_packet(flow = flow,
                                            outer_dst_mac = OUR_MAC,
                                            outer_src_mac = OUTER_SMAC,
                                            outer_dst_ip = VIP,
                                            outer_src_ip = SRC_VM_PA_IP,
                                            dst_udp_port = 80,
                                            src_udp_port = 11638,
                                            vni = 0xABA,
                                            inner_dst_mac = "02:02:02:02:02:02",
                                            inner_src_mac = ENI_MAC,
                                            inner_dst_ip = DST_CA_IP,
                                            inner_src_ip = SRC_VM_IP )

        print(cfg)

        api.set_config(cfg)
        dataplane.start_traffic()

        print("Expected\tTotal Tx\tTotal Rx")
        assert wait_for(lambda: metrics_ok(api, cfg)), "Metrics validation failed!"
        print("Test passed !")

    # @pytest.mark.skip
    def test_remove_vnet_config(self, confgen, dpu, dataplane):

        confgen.mergeParams(TEST_VNET_OUTBOUND_CONFIG)
        confgen.generate()

        for item in confgen.items():
            item['OP'] = 'remove'
            pprint(item)

        with (current_file_dir / 'test_vnet_outbound_cleanup_commands_simple.json').open(mode='r') as config_file:
            cleanup_commands = json.load(config_file)

        result = [*dpu.process_commands(cleanup_commands)]
        print("\n======= SAI commands RETURN values =======")
        pprint(result)

# Temporary func
def wait_for(func, timeout=10, interval=0.2):
    """
    Keeps calling the `func` until it returns true or `timeout` occurs
    every `interval` seconds.
    """

    start = time.time()

    while time.time() - start <= timeout:
        if func():
            return True
        time.sleep(interval)

    print("Timeout occurred !")
    return False

# Temporary func
def metrics_ok(api, cfg):
    # create a port metrics request and filter based on port names
    req = api.metrics_request()
    req.port.port_names = [p.name for p in cfg.ports]
    # include only sent and received packet counts
    req.port.column_names = [req.port.FRAMES_TX, req.port.FRAMES_RX]

    # fetch port metrics
    res = api.get_metrics(req)
    # calculate total frames sent and received across all configured ports
    total_tx = sum([m.frames_tx for m in res.port_metrics])
    total_rx = sum([m.frames_rx for m in res.port_metrics])
    expected = sum([f.duration.fixed_packets.packets for f in cfg.flows])

    print("%d\t\t%d\t\t%d" % (expected, total_tx, total_rx))

    return expected == total_tx and total_rx >= expected