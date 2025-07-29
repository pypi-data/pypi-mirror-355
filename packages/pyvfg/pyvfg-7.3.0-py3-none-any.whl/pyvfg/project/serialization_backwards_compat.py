# -*- coding: utf-8 -*-
import typing
from typing import Dict, List, Union, Any

from pathlib import Path
import io
import zipfile
import json
import numpy as np

from ..versions.vfg_0_5_0 import VFG as VFG_050

GeniusProjectFile = Union[str, typing.BinaryIO, Path]


def load_project_050(file: GeniusProjectFile) -> List[VFG_050]:
    """
    Backwards-compatible (0.5.0) handling of a VFG project file.
    Will load a Genius Project File into a VFG 0.5.0, with merged
    tensors.
    """

    def load_single_tensor(zf: zipfile.ZipFile, prefix: str, name: str) -> np.ndarray:
        """
        Loads a single tensor from the zip file, in the given prefix directory.
        """
        with zf.open(f"{prefix}/tensors/{name}.np", mode="r") as f:
            return np.load(f, allow_pickle=False, encoding="bytes")

    models = []
    with zipfile.ZipFile(file, "r") as zf:
        # read manifest at root level to see the list of models we have available
        with zf.open("manifest.txt", mode="r") as mf:
            model_prefixes: List[str] = [
                line.decode("utf-8").strip() for line in mf.readlines()
            ]

        # for each model name ("prefix") in the manifest
        for prefix in model_prefixes:
            # Get the JSON file
            with zf.open(f"{prefix}/vfg.json") as f:
                vfg_json: Dict[str, Any] = json.load(f)
            # Get the factor files
            if "factors" in vfg_json:
                for factor in vfg_json["factors"]:
                    if "counts" in factor and factor["counts"] is not None:
                        factor["counts"] = load_single_tensor(
                            zf, prefix, factor["counts"]
                        )
                    if "values" in factor and factor["values"] is not None:
                        factor["values"] = load_single_tensor(
                            zf, prefix, factor["values"]
                        )
            with zf.open(f"{prefix}/visualization_metadata.json") as f:
                # Load the visualization metadata
                viz_metadata = json.load(f)
                # Add the visualization metadata to the VFG
                vfg_json["visualization_metadata"] = viz_metadata
            # and finally, load the dict into a single model
            models.append(VFG_050.from_dict(vfg_json))
    # create the VFG from the JSON
    return models


def save_project_050(
    vfg: VFG_050, file: GeniusProjectFile, model_name: typing.Optional[str] = None
) -> None:
    """
    Backwards-compatible (0.5.0) saving of a VFG project file.
    Will save a VFG 0.5.0 into a Genius Project File, with externalized
    tensors.
    """
    if model_name is None:
        model_name = "model1"
    # create the NPZ file
    tensors = {}
    for factor in vfg.factors:
        factor_name = "-".join(factor.variables)
        if factor.counts is not None:
            # save the counts tensor to the NPZ file
            tensors[factor_name + "-counts"] = factor.counts
            # then clear so we don't waste time serializing
            factor.counts = np.empty((0,))
        if factor.values is not None:
            # save the values tensor to the NPZ file
            tensors[factor_name + "-values"] = factor.values
            # then clear so we don't waste time serializing
            factor.values = np.empty((0,))
    # create the JSON file
    vfg_json = vfg.model_dump()
    # fix up the vfg json with the factor values
    for factor in vfg_json["factors"]:
        if factor["variables"] is None:
            continue
        factor_name = "-".join(factor["variables"])
        if "counts" in factor and factor["counts"] is not None:
            factor["counts"] = factor_name + "-counts"
        if "values" in factor and factor["values"] is not None:
            factor["values"] = factor_name + "-values"
    # remove the visualization metadata
    if "visualization_metadata" in vfg_json:
        viz_metadata = vfg_json["visualization_metadata"]
        del vfg_json["visualization_metadata"]
    else:
        viz_metadata = {}

    # save the JSON and NPZ files
    with zipfile.ZipFile(file, "w") as zf:
        # write the manifest
        with zf.open("manifest.txt", mode="w") as mf:
            mf.write(f"{model_name}\n".encode("utf-8"))
        # write the model json, into the appropriate prefix
        with zf.open(f"{model_name}/vfg.json", mode="w") as f:
            text_stream = io.TextIOWrapper(f, encoding="utf-8", write_through=True)
            json.dump(vfg_json, text_stream)
        # write all tensors to the zip file, indexed by name
        for tensor_name, tensor in tensors.items():
            with zf.open(f"{model_name}/tensors/{tensor_name}.np", mode="w") as f:
                np.save(f, tensor)
        # write visualization metadata
        with zf.open(f"{model_name}/visualization_metadata.json", "w") as f:
            text_stream = io.TextIOWrapper(f, encoding="utf-8", write_through=True)
            json.dump(viz_metadata, text_stream)


def _add_if_not_in(list1: List[Any], list2: List[Any]) -> None:
    """
    Adds elements from list2 to list1 if they are not already present in list1.
    """
    for item in list2:
        if item not in list1:
            list1.append(item)


def merge_project_files(
    input_projects: List[GeniusProjectFile], output_project: GeniusProjectFile
) -> None:
    """
    Merges two or more project files into a single project file.
    The output file cannot be an input file.
    Later models in input will overwrite earlier models in input.
    """
    if output_project in input_projects:
        raise ValueError("Output file cannot be an input file")
    all_models = []
    with zipfile.ZipFile(output_project, "w") as outf:
        for input_fn in input_projects:
            with zipfile.ZipFile(input_fn, "r") as inf:
                # read manifest at root level to see the list of models we have available
                with inf.open("manifest.txt", mode="r") as mf:
                    _add_if_not_in(
                        all_models,
                        [line.decode("utf-8").strip() for line in mf.readlines()],
                    )
                for name in inf.namelist():
                    if name == "manifest.txt":
                        continue
                    # copy the file to the output file
                    outf.writestr(name, inf.read(name))
        outf.writestr("manifest.txt", "\n".join(all_models).encode("utf-8"))
