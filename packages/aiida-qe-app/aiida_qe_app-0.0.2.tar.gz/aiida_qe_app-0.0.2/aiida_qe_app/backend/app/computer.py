# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.querybuilder import QueryBuilder
from fastapi import APIRouter, HTTPException
from .models import Computer


router = APIRouter()


@router.get("/api/computers", response_model=List[Computer])
@with_dbenv()
async def read_computers() -> List[Computer]:
    """Get list of all computers"""

    return Computer.get_entities()


@router.get("/api/computers/projectable_properties", response_model=List[str])
async def get_computers_projectable_properties() -> List[str]:
    """Get projectable properties for computers endpoint"""

    return Computer.get_projectable_properties()


@router.get("/api/computers/{comp_id}", response_model=Computer)
@with_dbenv()
async def read_computer(comp_id: int) -> Optional[Computer]:
    """Get computer by id."""
    qbobj = QueryBuilder()
    qbobj.append(
        orm.Computer, filters={"id": comp_id}, project="**", tag="computer"
    ).limit(1)

    return qbobj.dict()[0]["computer"]


@router.post("/api/computers", status_code=201)
async def add_computer(computer_data: dict):
    # Check if the computer already exists
    from aiida.orm.utils.builders.computer import ComputerBuilder
    from aiida import orm
    from aiida.orm.querybuilder import QueryBuilder

    qb = QueryBuilder()
    qb.append(orm.Computer, filters={"label": computer_data["label"]})
    if qb.count() > 0:
        raise HTTPException(
            status_code=400,
            detail=f"A computer with label '{computer_data.label}' already exists.",
        )

    # Create the computer
    computer_builder = ComputerBuilder(**computer_data)
    # Validate and store the computer
    computer = computer_builder.new()
    computer.store()
    return {"message": "Computer added successfully!", "computer_id": computer.id}
