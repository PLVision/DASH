from pytest import fixture


@fixture
def testsbed():
    ...


def test_vnet(testsbed):
    dpu = testsbed.dpus['default']

    sai_erm = GenerateSAI.from_yaml(
        Path(__file__).parent/'sai_erm.yaml', use=[pre_config]
    )

    dpu.apply_sai_erm(sai_erm)
    dpu.remove_sai_erm(sai_erm)
