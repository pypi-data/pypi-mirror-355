# backend/app/api/endpoints.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aiida.engine import submit
from aiida.orm import StructureData, load_code
import traceback
from .utils import get_plugins


router = APIRouter()


class CalculationData(BaseModel):
    # Define the expected structure of the calculation data
    # Adjust fields as necessary to match the data sent from the front-end
    structure: dict
    workflow_settings: dict
    computational_resources: dict
    review_submit: dict


def get_pseudos(data):
    pseudos_settings = data.workflow_settings.get("Pseudopotential Settings", {})
    pseudo_family = pseudos_settings.get("pseudo_family", "SSSP/1.3/PBEsol/efficiency")
    pseudos = {}
    for symbol, pseudo_data in pseudos_settings["pseudos"].items():
        pseudos[symbol] = pseudo_data["uuid"]
    cutoffs = {
        "cutoff_wfc": pseudos_settings.get("wavefunctionCutoff", 30),
        "cutoff_rho": pseudos_settings.get("chargeDensityCutoff", 240),
    }
    return {"pseudo_family": pseudo_family, "pseudos": pseudos, "cutoffs": cutoffs}


def get_advanced_setting_value(data):

    # basic workflow settings
    parameters = {"workchain": {}, "advanced": {}}
    basic_settings = data.workflow_settings.get("Basic Settings", {})
    mapping = {
        "relax_type": "relaxType",
        "electronic_type": "electronicType",
        "spin_type": "spinType",
        "protocol": "protocol",
    }
    for key, value in mapping.items():
        parameters["workchain"][key] = basic_settings.pop(value, None)
    parameters["workchain"]["properties"] = (
        ["relax"] if parameters["workchain"]["relax_type"] != "none" else []
    )
    # all the remaining settings, which are True will be considered as properties
    for key, value in basic_settings["properties"].items():
        if value:
            parameters["workchain"]["properties"].append(key)
    # create the the initial_magnetic_moments as None (Default)
    # advanced settings
    advanced_settings = data.workflow_settings.get("Advanced Settings", {})
    parameters["advanced"] = {
        "initial_magnetic_moments": None,
        "pw": {
            "parameters": {
                "SYSTEM": {},
                "CONTROL": {},
                "ELECTRONS": {},
            },
            "pseudos": {},
        },
        "clean_workdir": advanced_settings.get("cleanUp", False),
        "pseudo_family": advanced_settings.get(
            "pseudoFamily", "SSSP/1.3/PBEsol/efficiency"
        ),
        "kpoints_distance": advanced_settings["kPointsDistance"],
    }
    # Set total charge
    # parameters["pw"]["parameters"]["SYSTEM"]["tot_charge"] = advanced_settings["totalCharge"]
    parameters["advanced"]["kpoints_distance"] = advanced_settings["kPointsDistance"]
    if parameters["workchain"]["electronic_type"] == "metal":
        # smearing type setting
        parameters["advanced"]["pw"]["parameters"]["SYSTEM"][
            "smearing"
        ] = advanced_settings["smearingType"]
        # smearing degauss setting
        parameters["advanced"]["pw"]["parameters"]["SYSTEM"][
            "degauss"
        ] = advanced_settings["smearingWidth"]
    # convergence threshold setting
    parameters["advanced"]["pw"]["parameters"]["CONTROL"][
        "forc_conv_thr"
    ] = advanced_settings["forceConvergence"]
    parameters["advanced"]["pw"]["parameters"]["ELECTRONS"][
        "conv_thr"
    ] = advanced_settings["scfConvergence"]
    parameters["advanced"]["pw"]["parameters"]["CONTROL"][
        "etot_conv_thr"
    ] = advanced_settings["energyConvergence"]
    # Spin-Orbit calculation
    if advanced_settings["spinOrbit"] == "soc":
        parameters["advanced"]["pw"]["parameters"]["SYSTEM"]["lspinorb"] = True
        parameters["advanced"]["pw"]["parameters"]["SYSTEM"]["noncolin"] = True
        parameters["advanced"]["pw"]["parameters"]["SYSTEM"]["nspin"] = 4
    # pseudos
    pseudos_data = get_pseudos(data)
    parameters["advanced"]["pseudo_family"] = pseudos_data["pseudo_family"]
    parameters["advanced"]["pw"]["pseudos"] = pseudos_data["pseudos"]
    parameters["advanced"]["pw"]["parameters"]["SYSTEM"]["ecutwfc"] = pseudos_data[
        "cutoffs"
    ]["cutoff_wfc"]
    parameters["advanced"]["pw"]["parameters"]["SYSTEM"]["ecutrho"] = pseudos_data[
        "cutoffs"
    ]["cutoff_rho"]

    return parameters


def get_codes_values(data):
    codes = {}
    for _, settings in data.computational_resources.items():
        for code_name, data in settings["codes"].items():
            label = data["label"]
            aiida_code = load_code(label)
            codes[code_name] = {
                "code": aiida_code.uuid,
                "nodes": data["nodes"],
                "ntasks_per_node": data["cpus"],
                "cpus_per_task": 1,
                "max_wallclock_seconds": data.get("max_wallclock_seconds", 3600),
            }

    return codes


def prepare_inputs(data: CalculationData):
    """
    Prepare inputs for the calculation
    """
    from ase import Atoms
    from copy import deepcopy

    data = deepcopy(data)
    print("data: ", data)
    # structure
    structure = data.structure["Structure Selection"]["selectedStructure"]
    if isinstance(structure, list):
        structure = structure[0]
    atoms = Atoms(
        symbols=structure["symbols"],
        positions=structure["positions"],
        cell=structure["cell"],
        pbc=structure["pbc"],
    )
    structure = StructureData(ase=atoms)
    structure.store()
    # workflow settings
    parameters = get_advanced_setting_value(data)
    # bands
    plugins = get_plugins()
    for prop in parameters["workchain"]["properties"]:
        if prop in plugins:
            parameters[prop] = plugins[prop]["get_tab_value"](
                data.workflow_settings.get(prop.capitalize() + " Settings", {})
            )
    # computational resources
    parameters["codes"] = get_codes_values(data)
    return {
        "structure": structure,
        "parameters": parameters,
    }


def update_builder(builder, codes):
    """Update the resources and parallelization of the ``relax`` builder."""
    # this is hardcoded for now, but in the future, the relax should be a plugin
    # update resources

    builder.relax.base.pw.metadata.options.resources = {
        "num_machines": codes.get("pw")["nodes"],
        "num_mpiprocs_per_machine": codes.get("pw")["ntasks_per_node"],
        "num_cores_per_mpiproc": codes.get("pw")["cpus_per_task"],
    }


@router.post("/api/submit_workchain")
async def submit_workchain(data: CalculationData):
    from aiida_qe_app.workflows.qeapp_workchain import QeAppWorkChain
    from aiida.orm.utils.serialize import serialize
    from copy import deepcopy

    try:
        # Process the data
        # For example, start the calculation using AiiDA
        # Return a success response with job details
        inputs = prepare_inputs(data)
        codes = deepcopy(inputs["parameters"]["codes"])
        builder = QeAppWorkChain.get_builder_from_protocol(**inputs)
        update_builder(builder, codes)
        process = submit(builder)
        data.review_submit["Label and Submit"]["jobId"] = process.pk
        process.base.extras.set("ui_parameters", serialize(data))
        # store the workchain name in extras, this will help to filter the workchain in the future
        process.base.extras.set("workchain", inputs["parameters"]["workchain"])
        process.base.extras.set("structure", inputs["structure"].get_formula())
        process.label = data.review_submit.get("Label and Submit", {})["label"]
        process.description = data.review_submit.get("Label and Submit", {})[
            "description"
        ]
        return {"status": "success", "job_id": process.pk}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/submit_workgraph")
async def submit_workgraph(data: CalculationData):
    from aiida_qe_app.workflows.qeapp_workgraph import qeapp_workgraph

    from aiida.orm.utils.serialize import serialize
    from copy import deepcopy

    try:
        # Process the data
        # For example, start the calculation using AiiDA
        # Return a success response with job details
        inputs = prepare_inputs(data)
        codes = deepcopy(inputs["parameters"]["codes"])
        print("inputs: ", inputs)
        wg = qeapp_workgraph(**inputs)
        if "relax" in wg.tasks:
            wg.tasks["relax"].set(
                {
                    "base.pw.metadata.options.resources": {
                        "num_machines": codes.get("pw")["nodes"],
                        "num_mpiprocs_per_machine": codes.get("pw")["ntasks_per_node"],
                        "num_cores_per_mpiproc": codes.get("pw")["cpus_per_task"],
                    }
                }
            )
        process = wg.submit()
        data.review_submit["Label and Submit"]["jobId"] = process.pk
        process.base.extras.set("ui_parameters", serialize(data))
        # store the workchain name in extras, this will help to filter the workchain in the future
        process.base.extras.set("workchain", inputs["parameters"]["workchain"])
        process.base.extras.set("structure", inputs["structure"].get_formula())
        process.label = data.review_submit.get("Label and Submit", {})["label"]
        process.description = data.review_submit.get("Label and Submit", {})[
            "description"
        ]
        return {"status": "success", "job_id": process.pk}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
