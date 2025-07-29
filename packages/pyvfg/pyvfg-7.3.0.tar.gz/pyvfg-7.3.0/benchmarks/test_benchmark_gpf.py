import pytest
from pathlib import Path

from pyvfg.project.serialization_backwards_compat import load_project_050
import pydantic_core

project_root = Path(__file__).parent.parent


@pytest.mark.parametrize(
    "vfg_file",
    [
        "taxi/taxi_vfg.json",
        "7500_lines_over_833_areas_transmission_network_23335_factors.json",
        "taxi_vfg_0_3_0.json",
    ],
)
@pytest.mark.benchmark(group="vfg_load")
def test_load_standalone_vfg(benchmark, vfg_file):
    path = str(project_root / "tests/fixtures/models" / vfg_file)

    def load():
        with open(path, "r") as f:
            return pydantic_core.from_json(f.read())

    vfg = benchmark(load)
    assert vfg is not None


@pytest.mark.parametrize(
    "gpf_file",
    [
        "taxi/taxi_vfg.gpf",
        "7500_lines_over_833_areas_transmission_network_23335_factors.gpf",
        "taxi_vfg_0_3_0.gpf",
    ],
)
@pytest.mark.benchmark(group="vfg_load")
def test_load_project_vfg(benchmark, gpf_file):
    path = project_root / "tests/fixtures/models" / gpf_file

    def load():
        projects = load_project_050(path)
        return projects

    vfgs = benchmark(load)
    assert vfgs is not None and len(vfgs) == 1
