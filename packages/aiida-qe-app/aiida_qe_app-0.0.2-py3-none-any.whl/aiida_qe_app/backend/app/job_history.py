from fastapi import APIRouter, HTTPException, Query
from aiida import orm
from typing import List, Dict, Union

router = APIRouter()


@router.get("/api/jobs-data")
async def read_job_data(search: str = Query(None)):
    from aiida_qe_app.workflows.qeapp_workchain import QeAppWorkChain
    from aiida_workgraph.engine.workgraph import WorkGraphEngine
    from aiida.orm import QueryBuilder

    try:
        projections = [
            "id",
            "extras.structure",
            "ctime",
            "attributes.process_state",
            "label",
            "extras.workchain.relax_type",
            "extras.workchain.properties",
        ]

        qb = QueryBuilder()
        qb.append(QeAppWorkChain, project=projections, tag="process")
        qb.order_by({"process": {"ctime": "desc"}})
        results = qb.all()
        data = []
        for p in results:
            data.append({projections[i]: p[i] for i in range(len(projections))})
        # query WorkGraphEngine with label WorkGraph<QeAppWorkGraph>
        qb = QueryBuilder()
        qb.append(
            WorkGraphEngine,
            project=projections,
            tag="process",
            filters={
                orm.WorkChainNode.fields.process_label: "WorkGraph<QeAppWorkGraph>"
            },
        )
        qb.order_by({"process": {"ctime": "desc"}})
        results = qb.all()
        for p in results:
            data.append({projections[i]: p[i] for i in range(len(projections))})
        return {"jobs": data}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Workgraph {id} not found")


@router.get("/api/jobs-data/{id}")
async def read_job(id: int):
    from aiida.orm.utils.serialize import deserialize_unsafe
    from aiida.cmdline.utils.ascii_vis import build_call_graph

    try:
        node = orm.load_node(id)
        content = deserialize_unsafe(node.base.extras.get("ui_parameters", ""))
        process_status = build_call_graph(node)
        # output structure
        structure = None
        if "relax" in node.base.links.get_outgoing().all_link_labels():
            relax_node = node.base.links.get_outgoing().get_node_by_label("relax")
            if "output_structure" in relax_node.outputs:
                structure = (
                    relax_node.outputs.output_structure.backend_entity.attributes
                )
        return {
            "stepsData": content,
            "processStatus": process_status,
            "structure": structure,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Workgraph {id} not found")


# Route for deleting a job item
@router.delete("/api/jobs-data/{id}")
async def delete_job(
    id: int,
    dry_run: bool = False,
) -> Dict[str, Union[bool, str, List[int]]]:
    from aiida.tools import delete_nodes

    try:
        # Perform the delete action here
        deleted_nodes, was_deleted = delete_nodes([id], dry_run=dry_run)
        if was_deleted:
            return {
                "deleted": True,
                "message": f"Deleted job {id}",
                "deleted_nodes": list(deleted_nodes),
            }
        else:
            message = f"Did not delete job {id}"
            if dry_run:
                message += " [dry-run]"
            return {
                "deleted": False,
                "message": message,
                "deleted_nodes": list(deleted_nodes),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
