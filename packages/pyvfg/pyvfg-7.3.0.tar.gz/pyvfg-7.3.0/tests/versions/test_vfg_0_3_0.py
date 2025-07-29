import json
from pyvfg import vfg_upgrade
from .conftest import package_dir


def test_vfg_030_from_json():
    file_path = (
        package_dir / "tests/fixtures/models" / "sprinkler/sprinkler_vfg_0_3_0.json"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    vfg = vfg_upgrade(data)

    assert vfg.version == "0.5.0"
    for factor, factor_data in zip(vfg.factors, data["factors"]):
        assert factor.variables == factor_data["variables"]
