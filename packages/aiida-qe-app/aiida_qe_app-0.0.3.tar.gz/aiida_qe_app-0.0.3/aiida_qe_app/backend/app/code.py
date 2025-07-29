# -*- coding: utf-8 -*-
"""Declaration of FastAPI application."""
from typing import List, Optional

from aiida import orm
from aiida.cmdline.utils.decorators import with_dbenv
from aiida.orm.querybuilder import QueryBuilder
from fastapi import APIRouter
from .models import Code


router = APIRouter()


@router.get("/api/codes", response_model=List[Code])
@with_dbenv()
async def read_codes() -> List[Code]:
    """Get list of all codes"""

    return Code.get_entities()


@router.get("/api/codes/projectable_properties", response_model=List[str])
async def get_codes_projectable_properties() -> List[str]:
    """Get projectable properties for codes endpoint"""

    return Code.get_projectable_properties()


@router.get("/api/codes/{comp_id}", response_model=Code)
@with_dbenv()
async def read_code(comp_id: int) -> Optional[Code]:
    """Get code by id."""
    qbobj = QueryBuilder()
    qbobj.append(orm.Code, filters={"id": comp_id}, project="**", tag="code").limit(1)

    return qbobj.dict()[0]["code"]


@router.post("/api/codes", response_model=Code)
@with_dbenv()
async def create_code(
    code: Code,
) -> Code:
    """Create new AiiDA code."""
    orm_code = orm.Code(**code.dict(exclude_unset=True)).store()

    return Code.from_orm(orm_code)
