from __future__ import annotations

import platform
import shlex

import click
from importlib_metadata import version
from textual.constants import DEVTOOLS_HOST, DEVTOOLS_PORT

from .tools.run import exec_command, run_app

WINDOWS = platform.system() == "Windows"
"""True if we're running on Windows."""


@click.group()
@click.version_option(version("textual"))
def run() -> None:
    pass


@run.command(help="Run the Textual Devtools console.")
@click.option(
    "--port",
    "port",
    type=int,
    default=None,
    metavar="PORT",
    help=f"Port to use for the development mode console. Defaults to {DEVTOOLS_PORT}.",
)
@click.option("-v", "verbose", help="Enable verbose logs.", is_flag=True)
@click.option("-x", "--exclude", "exclude", help="Exclude log group(s)", multiple=True)
def console(port: int | None, verbose: bool, exclude: list[str]) -> None:
    """Launch the textual console."""

    from rich.console import Console

    from textual_dev.server import _run_devtools

    console = Console()
    console.clear()
    console.show_cursor(False)
    try:
        _run_devtools(verbose=verbose, exclude=exclude, port=port)
    finally:
        console.show_cursor(True)


def _pre_run_warnings() -> None:
    """Look for and report any issues with the environment.

    This is the right place to add code that looks at the terminal, or other
    environmental issues, and if a problem is seen it should be printed so
    the developer can see it easily.
    """
    import os

    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    # Add any test/warning pair here. The list contains a tuple where the
    # first item is `True` if a problem situation is detected, and the
    # second item is a message to show the user on exit from `textual run`.
    warnings = [
        (
            (
                platform.system() == "Darwin"
                and os.environ.get("TERM_PROGRAM") == "Apple_Terminal"
            ),
            "The default terminal app on macOS is limited to 256 colors. See our FAQ for more details:\n\n"
            "https://textual.textualize.io/FAQ/#why-doesnt-textual-look-good-on-macos",
        )
    ]

    for concerning, concern in warnings:
        if concerning:
            console.print(
                Panel.fit(
                    f"⚠️  {concern}", style="yellow", border_style="red", padding=(1, 2)
                )
            )


@run.command(
    "run",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.argument("import_name", metavar="FILE or FILE:APP")
@click.option("--dev", "dev", help="Enable development mode.", is_flag=True)
@click.option(
    "--host",
    "host",
    type=str,
    default=None,
    metavar="HOST",
    help=f"Host where the development console is running. Defaults to {DEVTOOLS_HOST}.",
)
@click.option(
    "--port",
    "port",
    type=int,
    default=None,
    metavar="PORT",
    help=f"Port where the development console is running. Defaults to {DEVTOOLS_PORT}.",
)
@click.option(
    "--press", "press", default=None, help="Comma separated keys to simulate press."
)
@click.option(
    "--screenshot",
    type=int,
    default=None,
    metavar="DELAY",
    help="Take screenshot after DELAY seconds.",
)
@click.option(
    "-c",
    "--command",
    "command",
    type=bool,
    default=False,
    help="Run as command rather that a file / module.",
    is_flag=True,
)
@click.option(
    "-r",
    "--show-return",
    "show_return",
    type=bool,
    default=False,
    help="Show any return value on exit.",
    is_flag=True,
)
@click.argument("extra_args", nargs=-1, type=click.UNPROCESSED)
def _run_app(
    import_name: str,
    dev: bool,
    host: str | None,
    port: int | None,
    press: str | None,
    screenshot: int | None,
    extra_args: tuple[str],
    command: bool = False,
    show_return: bool = False,
) -> None:
    """Run a Textual app.

    The app to run may be given as a path (ending with .py) which will be equivalent to running the
    script with python, or as a Python import which will import and run an app called "app".

    In the case of an import, you can import and run an alternative app by appending a colon followed
    by the name of the app instance or class.

    Here are some examples:

        textual run foo.py

        textual run module.foo

        textual run module.foo:MyApp

    Add the --dev switch to enable the textual console.

        textual run --dev foo.py

    Use the -c switch to run a command that launches a Textual app.

        textual run -c textual colors

    """

    import os

    from textual.features import parse_features

    environment = dict(os.environ)

    features = set(parse_features(environment.get("TEXTUAL", "")))
    if dev:
        features.add("debug")
        features.add("devtools")

    environment["TEXTUAL"] = ",".join(sorted(features))
    if host is not None:
        environment["TEXTUAL_DEVTOOLS_HOST"] = str(host)
    if port is not None:
        environment["TEXTUAL_DEVTOOLS_PORT"] = str(port)
    if press is not None:
        environment["TEXTUAL_PRESS"] = str(press)
    if screenshot is not None:
        environment["TEXTUAL_SCREENSHOT"] = str(screenshot)
    if show_return:
        environment["TEXTUAL_SHOW_RETURN"] = "1"

    _pre_run_warnings()

    import_name, *args = [*shlex.split(import_name, posix=not WINDOWS), *extra_args]

    if command:
        exec_command(import_name, args, environment)
    else:
        run_app(import_name, args, environment)


@run.command("borders")
def borders() -> None:
    """Explore the border styles available in Textual."""
    from textual_dev.previews import BorderApp

    BorderApp().run()


@run.command("easing")
def easing() -> None:
    """Explore the animation easing functions available in Textual."""
    from textual_dev.previews import EasingApp

    EasingApp().run()


@run.command("colors")
def colors() -> None:
    """Explore the design system."""
    from textual_dev.previews import ColorsApp

    ColorsApp().run()


@run.command("keys")
def keys() -> None:
    """Show key events."""
    from textual_dev.previews import KeysApp

    KeysApp().run()


@run.command("diagnose")
def run_diagnose() -> None:
    """Print information about the Textual environment."""
    from textual_dev.tools.diagnose import diagnose

    diagnose()
