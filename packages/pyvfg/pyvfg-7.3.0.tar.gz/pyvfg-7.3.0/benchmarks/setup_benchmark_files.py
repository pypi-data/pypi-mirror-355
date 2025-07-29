# -*- coding: utf-8 -*-
from pyvfg.project.serialization_backwards_compat import save_project_050
from pyvfg.versions.vfg_0_5_0 import VFG
from pathlib import Path

models_base = Path(__file__).parent.parent / "tests/fixtures/models"

small_taxi_vfg = VFG.from_file(str(models_base / "taxi/taxi_vfg.json"))
save_project_050(
    vfg=small_taxi_vfg, file=models_base / "taxi/taxi_vfg.gpf", model_name="taxi"
)
transmission_vfg = VFG.from_file(
    str(
        models_base
        / "7500_lines_over_833_areas_transmission_network_23335_factors.json"
    )
)
save_project_050(
    vfg=transmission_vfg,
    file=models_base
    / "7500_lines_over_833_areas_transmission_network_23335_factors.gpf",
    model_name="transmission",
)
taxi_vfg = VFG.from_file(str(models_base / "taxi_vfg_0_3_0.json"))
save_project_050(
    vfg=taxi_vfg, file=models_base / "taxi_vfg_0_3_0.gpf", model_name="taxi_0_3_0"
)
