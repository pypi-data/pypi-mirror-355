from typing import ClassVar, List, Optional, Type, TypeVar, Tuple
from pydantic import BaseModel, Field, validator
from aiida import orm

ModelType = TypeVar("ModelType", bound="AiidaModel")


class AiidaModel(BaseModel):
    """A mapping of an AiiDA entity to a pydantic model."""

    _orm_entity: ClassVar[Type[orm.entities.Entity]] = orm.entities.Entity

    class Config:
        """The models configuration."""

        orm_mode = True
        extra = "forbid"

    @classmethod
    def get_projectable_properties(cls) -> List[str]:
        """Return projectable properties."""
        return list(cls.schema()["properties"].keys())

    @classmethod
    def get_entities(
        cls: Type[ModelType],
        *,
        page_size: Optional[int] = None,
        page: int = 0,
        project: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[ModelType]:
        """Return a list of entities (with pagination).

        :param project: properties to project (default: all available)
        :param page_size: the page size (default: infinite)
        :param page: the page to return, if page_size set
        """
        if project is None:
            project = cls.get_projectable_properties()
        else:
            assert set(cls.get_projectable_properties()).issuperset(
                project
            ), f"projection not subset of projectable properties: {project!r}"
        query = orm.QueryBuilder().append(
            cls._orm_entity, tag="fields", project=project
        )
        if page_size is not None:
            query.offset(page_size * (page - 1))
            query.limit(page_size)
        if order_by is not None:
            assert set(cls.get_projectable_properties()).issuperset(
                order_by
            ), f"order_by not subset of projectable properties: {project!r}"
            query.order_by({"fields": order_by})
        return [cls(**result["fields"]) for result in query.dict()]


class Computer(AiidaModel):
    """AiiDA Computer Model."""

    _orm_entity = orm.Computer

    id: Optional[int] = Field(description="Unique computer id (pk)")
    uuid: Optional[str] = Field(description="Unique id for computer")
    label: str = Field(description="Used to identify a computer. Must be unique")
    hostname: Optional[str] = Field(
        description="Label that identifies the computer within the network"
    )
    scheduler_type: Optional[str] = Field(
        description="The scheduler (and plugin) that the computer uses to manage jobs"
    )
    transport_type: Optional[str] = Field(
        description="The transport (and plugin) \
                    required to copy files and communicate to and from the computer"
    )
    metadata: Optional[dict] = Field(
        description="General settings for these communication and management protocols"
    )

    description: Optional[str] = Field(description="Description of node")


class ComputerCreateModel(BaseModel):
    label: str = Field(..., example="my_computer")
    hostname: str = Field(..., example="localhost")
    description: Optional[str] = Field("", example="Description of the computer")
    transport: str = Field(..., example="ssh")
    scheduler: str = Field(..., example="slurm")
    workdir: str = Field(..., example="/scratch/{username}/aiida_run")
    shebang: Optional[str] = Field("#!/bin/bash", example="#!/bin/bash")
    mpirun_command: Optional[List[str]] = Field(
        ["mpirun", "-np", "{tot_num_mpiprocs}"],
        example=["mpirun", "-np", "{tot_num_mpiprocs}"],
    )
    mpiprocs_per_machine: Optional[int] = Field(None, example=16)
    default_memory_per_machine: Optional[float] = Field(None, example=64.0)
    prepend_text: Optional[str] = Field("", example="module load mpi")
    append_text: Optional[str] = Field("", example="echo 'Done'")

    @validator("mpirun_command")
    def check_mpirun_command(cls, v):
        if not isinstance(v, list):
            raise ValueError("mpirun_command must be a list of strings")
        return v


class Code(AiidaModel):
    """AiiDA Code Model."""

    _orm_entity = orm.Code

    id: Optional[int] = Field(description="Unique code id (pk)")
    uuid: Optional[str] = Field(description="Unique UUID for the code")
    label: str = Field(description="Label to identify the code. Must be unique")
    description: Optional[str] = Field(description="Description of the code")
    dbcomputer_id: Optional[int] = Field(description="ID of the computer")
    attributes: Optional[dict] = Field(description="Additional attributes for the code")
    extras: Optional[dict] = Field(description="Additional extras for the code")

    @classmethod
    def get_entities(cls, **kwargs) -> List["Code"]:
        """Return a list of codes."""
        results = super().get_entities(**kwargs)
        # load the computer for each code
        for result in results:
            result.extras["computer"] = orm.load_computer(result.dbcomputer_id).label
        return results


class StructureModel(BaseModel):
    symbols: List[str]
    pbc: Optional[Tuple[bool, bool, bool]] = (
        True,
        True,
        True,
    )  # Periodic boundary conditions
