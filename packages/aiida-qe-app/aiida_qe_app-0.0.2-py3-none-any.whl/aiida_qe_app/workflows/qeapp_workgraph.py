from aiida_workgraph import WorkGraph, task
from aiida import orm
from aiida_quantumespresso.workflows.pw.relax import PwRelaxWorkChain
from aiida_quantumespresso.common.types import ElectronicType, RelaxType, SpinType
from aiida_quantumespresso.data.hubbard_structure import HubbardStructureData
from aiida_qe_app.utils import plugin_entries
import copy


def prepare_hubbard_structure(structure, hubbard_dict):
    """Prepare a HubbardStructureData node from a StructureData node and a dictionary of Hubbard U values."""
    # Check if hubbard_dict is provided
    if hubbard_dict is not None:
        hubbard_parameters = hubbard_dict["hubbard_u"]
        hubbard_structure = HubbardStructureData.from_structure(structure)
        # Initialize on-site Hubbard values
        for key, value in hubbard_parameters.items():
            kind, orbital = key.rsplit(" - ", 1)
            hubbard_structure.initialize_onsites_hubbard(
                atom_name=kind,
                atom_manifold=orbital,
                value=value,
                hubbard_type="U",
                use_kinds=True,
            )
        # Determine whether to store and use hubbard_structure based on conditions
        if (
            isinstance(structure, HubbardStructureData)
            and hubbard_structure.hubbard == structure.hubbard
        ):
            # If the structure is HubbardStructureData and hubbard parameters match, assign the original structure
            return structure
        else:
            # In all other cases, store and assign hubbard_structure
            hubbard_structure.store()
            return hubbard_structure
    elif isinstance(structure, HubbardStructureData):
        # Convert HubbardStructureData to a simple StructureData
        temp_structure = structure.get_ase()
        new_structure = orm.StructureData(ase=temp_structure)
        new_structure.store()
        return new_structure
    else:
        return structure


def prepare_relax_inputs(structure, codes, parameters, protocol, **kwargs):
    """Prepare inputs for the relax workchain."""
    relax_overrides = {
        "base": parameters["advanced"],
        "base_final_scf": parameters["advanced"],
    }
    relax_builder = PwRelaxWorkChain.get_builder_from_protocol(
        code=codes.get("pw")["code"],
        structure=structure,
        protocol=protocol,
        relax_type=RelaxType(parameters["workchain"]["relax_type"]),
        electronic_type=ElectronicType(parameters["workchain"]["electronic_type"]),
        spin_type=SpinType(parameters["workchain"]["spin_type"]),
        initial_magnetic_moments=parameters["advanced"]["initial_magnetic_moments"],
        overrides=relax_overrides,
        **kwargs,
    )
    # pop the inputs that are excluded from the expose_inputs
    relax_builder.pop("clean_workdir", None)
    relax_builder.pop("base_final_scf", None)  # never run a final scf
    return relax_builder


@task()
def inspect_relax(parameters):
    """Inspect relax calculation."""
    return parameters["number_of_bands"]


def get_inputs_from_builder(builder):
    """"""
    from aiida.engine.processes.builder import ProcessBuilderNamespace

    inputs = {}
    for key, value in builder.items():
        if isinstance(value, ProcessBuilderNamespace):
            if len(value) > 0:
                inputs[key] = get_inputs_from_builder(value)
        else:
            inputs[key] = value
    return inputs


@task.graph_builder()
def qeapp_workgraph(
    structure: orm.StructureData = None,
    parameters: orm.Dict = None,
) -> WorkGraph:
    """BandsWorkGraph."""
    parameters = {} if parameters is None else parameters
    properties = parameters["workchain"].pop("properties", [])
    protocol = parameters["workchain"]["protocol"]
    codes = parameters.pop("codes", {})
    # load codes from uuid
    for _, value in codes.items():
        if value["code"] is not None:
            value["code"] = orm.load_node(value["code"])
    # update pseudos
    for kind, uuid in parameters["advanced"]["pw"]["pseudos"].items():
        parameters["advanced"]["pw"]["pseudos"][kind] = orm.load_node(uuid)
    # Set a HubbardStructureData if hubbard_parameters is specified
    hubbard_dict = parameters["advanced"].pop("hubbard_parameters", None)
    structure = prepare_hubbard_structure(structure, hubbard_dict)
    # Initialize the workgraph
    wg = WorkGraph("QeAppWorkGraph")
    # Initialize some variables which can be overridden in the following
    current_structure = structure
    # current_number_of_bands = None
    # ------- relax -----------
    if "relax" in properties:
        relax_task = wg.add_task(PwRelaxWorkChain, name="relax")
        relax_builder = prepare_relax_inputs(
            structure=structure,
            codes=codes,
            parameters=parameters,
            protocol=protocol,
        )
        # retrieve the relax inputs from the inputs, and set the relax inputs
        relax_task.set(get_inputs_from_builder(relax_builder))
        # override the input structure with the relaxed structure
        current_structure = relax_task.outputs["output_structure"]
        # -------- inspect_relax -----------
        wg.add_task(
            inspect_relax,
            name="inspect_relax",
            parameters=relax_task.outputs["output_parameters"],
        )
        # current_number_of_bands = inspect_relax_task.outputs["result"]
    # -------- plugins -----------
    # add plugin workchain
    for name, entry_point in plugin_entries.items():
        if name in properties:
            plugin_builder = entry_point["get_builder"](
                codes, structure, copy.deepcopy(parameters)
            )
            plugin_task = wg.add_task(entry_point["workchain"], name=name)
            if "inspect_relax" in wg.tasks:
                plugin_task.waiting_on.add(["inspect_relax"])
            # this is hard coded for now, but we can make it more general
            # in the plugin, we can define a prepare_inputs function
            plugin_task.set(get_inputs_from_builder(plugin_builder))
            # set the structure for the plugin
            if "structure" in plugin_task.inputs:
                plugin_task.set({"structure": current_structure})

    return wg
