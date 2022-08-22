from pytest import fixture
from dataplane.ptf_testutils import verify_packets, send_packet, simple_tcp_packet


@fixture
def testsbed():
    ...



def test_vnet(testsbed):
    dpu = testsbed.dpus['default']

    sai_erm = GenerateSAI(
        {'IPv4': [
            {'vip': '10.10.1.1'},
            {'pa_validation_sip': '10.10.2.10'},
            {'pa_validation_dip': '10.10.2.20'}
        ],
         'MAC': [{'eni_mac': '00:00:00:09:03:14'}],
         'VIP': [{'vip': {'IPv4': '$vip'}}],
         'VNI': [
             {'vni': 60},
             {'inbound_routing_vni': 2}
         ],
         'DIRECTION_LOOKUP': [{'direction_lookup': {'VNI': '$vni'}}],
         'DASH_ACL': [
             {'acl_in': {'ADDR_FAMILY': 'IPv4'}},
             {'acl_out': {'ADDR_FAMILY': 'IPv4'}}
         ],
         'DASH_VNET': [{'vnet': {'VNI': '$vni'}}],
         'DASH_ENI': [
             {'eni': {'CPS': 10000,
                      'PPS': 100000,
                      'FLOWS': 10000,
                      'ADMIN_STATE': True,
                      'VM_UNDERLAY_DIP': '$pa_validation_dip',
                      'VM_VNI': 9,
                      'ACL_GROUP': {
                          'INBOUND': [
                              {'STAGE1': '$acl_in'},
                              {'STAGE2': '$acl_in'},
                              {'STAGE3': '$acl_in'},
                              {'STAGE4': '$acl_in'},
                              {'STAGE5': '$acl_in'}
                          ],
                          'OUTBOUND': [
                              {'STAGE1': '$acl_out'},
                              {'STAGE2': '$acl_out'},
                              {'STAGE3': '$acl_out'},
                              {'STAGE4': '$acl_out'},
                              {'STAGE5': '$acl_out'}
                          ]
                      }}}
         ],
         'ENI_ETHER_ADDRESS_MAP': [
             {'address_map': {'VNI': '$inbound_routing_vni', 'MAC': '$eni_mac'}}
         ],
         'INBOUND_ROUTING': [
             {'inbound_routing': {'VNI': '$inbound_routing_vni'}}
         ]
        }
    )

    dpu.apply_sai_erm(sai_erm)
    dpu.remove_sai_erm(sai_erm)
