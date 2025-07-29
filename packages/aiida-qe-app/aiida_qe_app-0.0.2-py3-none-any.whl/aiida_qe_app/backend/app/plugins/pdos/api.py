from fastapi import APIRouter, HTTPException
from aiida import orm
from aiida_qe_app.backend.app.plugins.electronic_structure.utils import (
    get_pdos_data_from_node,
)

router = APIRouter()


@router.get("/api/pdos/{id}")
async def get_pdos_data(id: int):

    try:
        node = orm.load_node(id)
        # output structure
        structure = None
        if "relax" in node.base.links.get_outgoing().all_link_labels():
            relax_node = node.base.links.get_outgoing().get_node_by_label("relax")
            if "output_structure" in relax_node.outputs:
                structure = (
                    relax_node.outputs.output_structure.backend_entity.attributes
                )

        # pdos
        pdos_data = None
        if "pdos" in node.base.links.get_outgoing().all_link_labels():
            pdos_node = node.base.links.get_outgoing().get_node_by_label("pdos")
            pdos_data = get_pdos_data_from_node(pdos_node)

        # Return the data as JSON
        data = {"structure": structure, "pdos_data": pdos_data}
        return data
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Process {id} not found")
