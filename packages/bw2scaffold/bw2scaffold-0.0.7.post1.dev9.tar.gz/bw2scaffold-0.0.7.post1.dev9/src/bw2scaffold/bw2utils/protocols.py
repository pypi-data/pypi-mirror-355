from typing import Any, Mapping, Protocol, Union, runtime_checkable

from . import logging

logger = logging.getLogger(__name__)

# TODO: Finish bw2data protocols and validators to ensure robustness among version


@runtime_checkable
class BW2DatabasesContainer(Protocol):
    """Interface of bw2data.databases agnostic to bw2data versions"""

    filename: str

    def __getitem__(self, database_name: str) -> Mapping:
        ...


def ValidateDatabasesContainer(databases: Any) -> Any:
    """Verifies databases footprint"""
    try:
        assert isinstance(
            databases, BW2DatabasesContainer
        ), f"{databases} is not a compatible {BW2DatabasesContainer} type"
        return databases
    except AssertionError:
        logger.error(
            "The databases container has an incompatible footprint "
            "[bold blue]hint: [/] downgrade your [b]bw2data[/] version]"
        )


def bw2data_databases_importer() -> Union[BW2DatabasesContainer, None]:
    try:
        import bw2data  # type: ignore

        databases = ValidateDatabasesContainer(bw2data.databases)
        return databases
    except ImportError:
        logger.error(
            "Failed to import bw2data. "
            "[bold blue]hint:[/] install it by doing `[b]pip install bw2data[/]`"
        )
        return None
