# © [2024] Luxembourg Institute of Science and Technology. All Rights Reserved
import logging
import os
from pathlib import Path
from subprocess import run
from typing import Any, Dict, Literal, Union

import yaml
from jinja2 import Environment, PackageLoader
from rich.progress import Progress, SpinnerColumn, TextColumn

logger = logging.getLogger(__name__)

# TODO try with minimum-dependencies


ENV = Environment(
    loader=PackageLoader("bw2scaffold", "templates"),
)

# Global variable
TEMPLATE_PARAMS = {}


def get_dependencies(manager: Union[Literal["conda"], Literal["pip"]]):
    """Gets current dependencies from conda and pip.

    Returns:
        conda_str: conda string corresponding to ``environment.yaml``
        pip_str: pip dependencies corresponding to ``requirements.txt``.

    """
    if manager == "conda":
        try:
            proc = run(
                [
                    "conda",
                    "env",
                    "export",
                    "--name",
                    os.environ["CONDA_DEFAULT_ENV"],
                    "--no-builds",
                ],
                text=True,
                capture_output=True,
            ).stdout

        except Exception:
            logger.warning("no conda env identified")
            proc = None

    if manager == "pip":

        proc = run(
            [
                "pip",
                "list",
                "--format=freeze",
            ],
            text=True,
            capture_output=True,
        ).stdout

    return proc


def parse_template(name: str, template_params: Dict[str, Any]) -> str:
    """Renders a template from a jinja2 template.

    Uses :py:mod:`jinja2` templates to render a new file using\
    the `template_params` dict.

    Args:
        name: Name of the jinja2 template with a ``*.template`` extension.

        template_params: Contains a dict of parameters of all templates.

    Returns:
        raw_file: Rendered string content that will be written into a file.
    """

    template = ENV.get_template(
        name,
    )

    return template.render(**template_params)


def create_node(nodes: Union[dict], parent: Path):
    """Iterates through a structure dict and creates the node file.

    #TODO: verify that the nodes are possible to create.

    Args:
        nodes: Dict containing the tree structure of the folders that will be created.
        parent: Absolute path of the parent path that will \
        contain the `nodes` tree substructure.
    """
    for name, node in nodes.items():
        if isinstance(node, dict):
            sub_parent = parent / name
            create_node(node, sub_parent)

        else:
            """
            The final leaf of the tree has the file name as \
            key and the template name as value, e.g.,:
            {'README.md': 'README.md.template' }
            """

            parent.mkdir(parents=True, exist_ok=True)
            if name == "environment.yaml":
                TEMPLATE_PARAMS["dependencies_conda"] = get_dependencies("conda")
            if name == "requirements.txt":
                TEMPLATE_PARAMS["dependencies_pip"] = get_dependencies("pip")

            with open((parent / name), encoding="utf-8", mode="w") as f:
                f.write(parse_template(node, TEMPLATE_PARAMS))


def create_structure(project_name: Path, parameters: dict = {}):
    """Creates a tree of folder as suggested by the lca-protocol

    Args:
        project_name: Path with location of the new project folder
        parameters: Parameters to feed into the template
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:

        progress.add_task(description="Creating folders...", total=None)
        nodes = yaml.safe_load(
            ENV.get_template("directories.yaml").render(**parameters)
        )
        create_node(nodes, project_name)


def create_env_vars(project_name: Path):
    """Creates a .env file containing environmental variables specific to the project"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:

        progress.add_task(description="Setting environmental variables...", total=None)

        # TODO: This should read a template of environmental variables
        BRIGHTWAY2_DIR = ".bw2projects"
        path_projects = project_name.absolute() / f"{BRIGHTWAY2_DIR}"
        path_projects.mkdir(parents=True, exist_ok=True)
        env_vars = [
            f"BRIGHTWAY2_DIR={path_projects}\n",
            f"export BRIGHTWAY2_DIR={path_projects}\n",
            "AUTOENV_ENABLE_LEAVE=True\n",
        ]

        with open(project_name / ".env", "w") as f:
            f.writelines(env_vars)

        env_leave_vars = ["unset AUTOENV_ENABLE_LEAVE\n", "unset BRIGHTWAY2_DIR\n"]

        with open(project_name / ".env.leave", "w") as f:
            f.writelines(env_leave_vars)
