from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
    RootModel,
    TypeAdapter,
    model_validator,
)
from typing_extensions import Annotated, Self

# from .protocols import bw2data_databases_importer, BW2DatabasesContainer
from . import logging

logger = logging.getLogger(__name__)

# TODO: Build data validators for ecoinvent and ecoinvent-act-type combinations
# TODO: Build data validators for reading yaml files (from list to tuple)


class CharacterizationFactorEcoInvent(BaseModel):
    method: str
    category: str
    indicator: str
    name: str
    compartment: str
    subcompartment: str
    cf: Union[float, Literal["NA"]] = Field(default="NA")  # NA represents a placeholder

    # based on: https://docs.pydantic.dev/latest/concepts/models/#validating-data
    model_config = ConfigDict(revalidate_instances="always")


class BWNode(BaseModel):
    categories: Optional[Tuple[str, str]] = None
    code: str
    name: str
    cas_number: Annotated[
        Optional[str],
        Field(validation_alias="CAS number", serialization_alias="CAS number"),
    ] = None
    unit: Optional[str] = None
    filename: Optional[FilePath] = None
    synonyms: Optional[List[str]] = []
    database: str
    parameters: Optional[List[Dict]] = None
    reference_product: Annotated[
        Optional[str],
        Field(
            validation_alias="reference product",
            serialization_alias="reference product",
        ),
    ] = None
    production_amount: Annotated[
        Optional[str],
        Field(
            validation_alias="production amount",
            serialization_alias="production amount",
        ),
    ] = None
    activity_type: Annotated[
        Optional[
            Literal[
                "market activity",
                "market group",
                "ordinary transforming activity",
                "production mix",
                None,
            ]
        ],
        Field(
            validation_alias="activity type",
            serialization_alias="activity type",
        ),
    ] = None
    type: Literal[
        "emission",
        "economic",
        "inventory indicator",
        "natural resource",
        "process",
        None,
    ] = None
    exchanges: Optional[List[Any]] = []

    # To set by_alias permanently as shown in:
    # https://stackoverflow.com/questions/78319788/\
    # how-to-make-serialization-alias-the-default-behavior-in-pydantic-basemodel
    def model_dump(self, **kwargs) -> dict[str, Any]:
        return super().model_dump(by_alias=True, **kwargs)

    # based on: https://docs.pydantic.dev/latest/concepts/models/#validating-data
    model_config = ConfigDict(
        revalidate_instances="always", extra="allow", populate_by_name=True
    )

    @model_validator(mode="after")
    def validate_ei_biosphere_node(self) -> Self:
        ei_biosphere_types = [
            "emission",
            "economic",
            "inventory indicator",
            "natural resource",
        ]
        categories_type: TypeAdapter = TypeAdapter(Tuple["str", "str"])

        if self.type in ei_biosphere_types:
            try:
                assert categories_type.validate_python(self.categories)
            except AssertionError:
                logger.error(
                    "This `seems` to be a biosphere node."
                    "The field `categories` is missing"
                )
        return self

    # TODO: Build database validator. It should alert if a database does not exist.


#     @field_validator('database')
#     @classmethod
#     def check_database_existance(cls, database_name:str) -> str: ...


BWDatabaseDict = RootModel[Dict[Tuple[str, str], BWNode]]
