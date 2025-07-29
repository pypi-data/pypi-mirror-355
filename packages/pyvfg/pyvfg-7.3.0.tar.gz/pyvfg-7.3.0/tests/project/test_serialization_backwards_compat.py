# -*- coding: utf-8 -*-
import unittest

import pathlib
import json
import io
import zipfile

from pyvfg.project.serialization_backwards_compat import merge_project_files
from pyvfg.versions.vfg_0_5_0 import VFG as VFG_050

PAYLOADS_PATH = pathlib.Path(__file__).parent.parent / "payloads/validate"


class MyTestCase(unittest.TestCase):
    @staticmethod
    def test_round_trip():
        """
        Tests round-trip creation of a VFG file to a project file and back. Ensures that, at a base level,
        this serialization format functions.
        """
        from pyvfg.project import load_project_050, save_project_050

        # Load the VFG file
        with open(PAYLOADS_PATH / "post_validate_example.json", "r") as f:
            vfg: VFG_050 = VFG_050.from_dict(json.load(f))
        vfg.validate(raise_exceptions=True)
        # Serialize to project file
        project_file = io.BytesIO()
        # NOTE: save_project_050 manipulates the tensors IN PLACE, so we'll have to get a clean version later
        save_project_050(vfg=vfg, file=project_file)
        assert project_file.tell() != 0, "assert that at least some data was written"

        # Test deserialization
        project_file.seek(0)
        models = load_project_050(file=project_file)
        assert len(models) == 1, "assert that we have one model"
        assert isinstance(models[0], VFG_050), "assert that we have a VFG_050 model"

        # Compare original and new json files using jsonpatch
        MyTestCase._compare_model(models[0], "post_validate_example.json")

    @staticmethod
    def test_multiple_projects():
        """
        Tests round-trip creation of a VFG file to a project file and back. Ensures that, at a base level,
        this serialization format functions.
        """
        from pyvfg.project import load_project_050, save_project_050

        # Load the VFG file
        with open(PAYLOADS_PATH / "post_validate_example.json", "r") as f:
            vfg: VFG_050 = VFG_050.from_dict(json.load(f))
        vfg.validate(raise_exceptions=True)
        # Serialize to project file
        project_file = io.BytesIO()
        # NOTE: save_project_050 manipulates the tensors IN PLACE, so we'll have to get a clean version later
        save_project_050(vfg=vfg, file=project_file)
        assert project_file.tell() != 0, "assert that at least some data was written"

        with open(PAYLOADS_PATH / "post_validate_example2.json", "r") as f:
            vfg: VFG_050 = VFG_050.from_dict(json.load(f))
        project_file_2 = io.BytesIO()
        save_project_050(vfg=vfg, file=project_file_2, model_name="model2")
        assert project_file_2.tell() != 0, "assert that at least some data was written"

        # Test merge
        project_file.seek(0)
        project_file_2.seek(0)
        merged_projects = io.BytesIO()
        merge_project_files([project_file, project_file_2], merged_projects)
        assert merged_projects.tell() != 0, "assert that at least some data was written"

        # Test manifest
        merged_projects.seek(0)
        with zipfile.ZipFile(merged_projects, "r") as zf:
            with zf.open("manifest.txt") as mf:
                manifest = [line.decode("utf").strip() for line in mf.readlines()]
                assert manifest[0] == "model1", "assert that the first model is model1"
                assert manifest[1] == "model2", "assert that the second model is model2"

        # Test deserialization
        merged_projects.seek(0)
        models = load_project_050(file=merged_projects)
        assert len(models) == 2, "assert that we have two models"
        assert isinstance(models[0], VFG_050), "assert that we have a VFG_050 model"
        assert isinstance(models[1], VFG_050), "assert that we have a VFG_050 model"
        # Compare original and new json files using jsonpatch
        MyTestCase._compare_model(models[0], "post_validate_example.json")
        MyTestCase._compare_model(models[1], "post_validate_example2.json")

    @staticmethod
    def _compare_model(model: VFG_050, file: str):
        with open(PAYLOADS_PATH / file, "r") as f:
            vfg: VFG_050 = VFG_050.from_dict(json.load(f))
        orig = json.loads(vfg.model_dump_json())
        new = json.loads(model.model_dump_json())
        assert orig == new, "Checking for no difference"


if __name__ == "__main__":
    unittest.main()
