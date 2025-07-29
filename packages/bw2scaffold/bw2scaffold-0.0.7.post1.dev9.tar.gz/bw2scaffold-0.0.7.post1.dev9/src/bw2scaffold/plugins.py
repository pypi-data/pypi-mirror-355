import logging
import os
import platform
from pathlib import Path
from subprocess import run

logger = logging.getLogger(__name__)


def install_autenv() -> None:
    """Install autoenv to manage environmental variables automatically

    Autoenv works in UNIX systems, it uses a .sh file to be activated \
    and it modifies the ~/.zshrc or  ~/.bashrc.
    See more here https://github.com/hyperupcall/autoenv
    """
    UNIX_AUTOENV_PATH = f"{os.getenv('HOME')}/.autoenv"
    # Get OS
    if "Linux" in platform.system():
        # Verify if '~/.autoenv' exists
        if Path(UNIX_AUTOENV_PATH).exists():
            logger.warning("autoenv already installed [bold yellow](skipping)[/]")
            return

        if "zsh" in Path(str(os.getenv("SHELL"))).name:
            run(
                "git clone "
                f"'https://github.com/hyperupcall/autoenv' {UNIX_AUTOENV_PATH}",
                shell=True,
            )
            run(
                "printf '%s\n' " "'source ~/.autoenv/activate.sh' >> ~/.zshrc",
                shell=True,
            )
        if "bash" in Path(str(os.getenv("SHELL"))).name:
            run(
                "git clone "
                f"'https://github.com/hyperupcall/autoenv' {UNIX_AUTOENV_PATH}",
                shell=True,
            )
            run(
                "printf '%s\n' 'source ~/.autoenv/activate.sh' >> ~/.bashrc",
                shell=True,
            )
        logger.info(f"Autoenv installed in: {UNIX_AUTOENV_PATH}")
        return
    else:
        logger.error(
            "Autoenv works only in UNIX-like systems [bold yellow](skipping)[/]",
            extra={"markup": True},
        )


def install_graphviz() -> None:
    """Install graphviz to plot callgraph

    Graphviz requires sudo rights.  Why bypass it by installing an conda-forge built
    Remember to use conda-forge channel
    """
    # Get OS
    if "Linux" in platform.system():

        if "zsh" in Path(str(os.getenv("SHELL"))).name:
            run(
                "conda install conda-forge::graphviz",
                shell=True,
            )
        if "bash" in Path(str(os.getenv("SHELL"))).name:
            run(
                "conda",
                "install",
                "conda-forge::graphviz",
                shell=True,
            )
        logger.info("Graphviz is installed")
        return
    else:
        logger.error(
            "Graphviz works only in UNIX-like systems [bold yellow](skipping)[/]",
            extra={"markup": True},
        )
