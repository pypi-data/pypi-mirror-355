# %%
# © [2024] Luxembourg Institute of Science and Technology. All Rights Reserved
"""
Command Line Interface for bw2scaffold
"""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from .bw2utils import logging
from .directories import create_env_vars, create_structure
from .plugins import install_autenv, install_graphviz
from .prepare import create_callgraph

# import logging

logger = logging.getLogger("bw2scaffold")

app = typer.Typer(rich_markup_mode="rich")


@app.command(
    help="[bold red]Packs up[/bold red] a project created with "
    "bw2scaffold and verifies its quality."
)
def finish(
    input_file: Annotated[str, typer.Argument(help="Path of run.py")],
    output_file: Annotated[
        str, typer.Argument(help="Path to export the callgraph")
    ] = "data/callgraph.png",
    function: Annotated[
        str,
        typer.Option(
            "--function",
            "-func",
            help="Name of the function containing the main pipeline",
        ),
    ] = "main",
):
    """Pack up a repository created with bw2scaffold and verifies its quality.

    This command is underdevelopment. It only generates a callgraph.
    """
    create_callgraph(input_file, output_file, function)

    logger.info(
        ":sparkles:[bold green]Success![/bold green] "
        ":package: :heavy_check_mark: Your project has been "
        "checked and packed :heavy_check_mark: :package:"
    )


@app.command(
    help="[bold green]Prepares[/bold green] a "
    "[link=https://docs.brightway.dev/][u]brightway[/u][/link] project template "
    "and starts your LCA modelling."
)
def start(
    project_name: Annotated[str, typer.Argument()],
    plugins: Annotated[
        Optional[bool],
        typer.Option(
            "--full",
            "-f",
            help=(
                "Installs recommended shell plugins that facilitate work. "
                "Works only in UNIX-like systems"
            ),
        ),
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Activate to have verbose logging")
    ] = False,
    email: Annotated[Optional[str], typer.Option()] = None,
):
    """Prepares a brightway project template and start your LCA modelling.

    This command creates an LCA template project compatible with the
    brightway software ecosystem.

    """
    logger = logging.getLogger("bw2scaffold", debug=verbose)

    parent = Path() / project_name
    create_structure(parent)
    create_env_vars(parent)
    logger.info(
        f":sparkles:[bold green]Success![/bold green] your "
        f"brightway-based repo has been created at: \n \n {parent.resolve()} \n"
    )

    if plugins:
        logger.debug("Installing plugins")
        install_autenv()
        install_graphviz()


def run():
    app()
