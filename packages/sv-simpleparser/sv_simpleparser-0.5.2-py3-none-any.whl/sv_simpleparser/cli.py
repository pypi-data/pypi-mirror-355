# MIT License
#
# Copyright (c) 2025 ericsmacedo
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Command Line Interface."""

import logging
import sys
from pathlib import Path

import click
from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.logging import RichHandler

from ._gen_templates import gen_instance, gen_markdown_table
from .parser import parse_file

_LOGLEVELMAP = {
    0: logging.WARNING,
    1: logging.INFO,
    2: logging.DEBUG,
}


arg_filepath = click.argument("file_path", type=click.Path(exists=True, readable=True, path_type=Path))


def _create_console(**kwargs) -> Console:
    return Console(**kwargs)


class Ctx(BaseModel):
    """Command Line Context."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )

    console: Console

    verbose: int = 0
    no_color: bool | None = None

    @staticmethod
    def create(no_color: bool | None = None, **kwargs) -> "Ctx":
        """Create."""
        console = _create_console(log_time=False, log_path=False, no_color=no_color)
        return Ctx(console=console, no_color=no_color, **kwargs)

    def __enter__(self):
        # Logging
        level = _LOGLEVELMAP.get(self.verbose, logging.DEBUG)
        if not self.no_color:
            handler = RichHandler(
                show_time=False,
                show_path=False,
                rich_tracebacks=True,
                console=_create_console(stderr=True, no_color=self.no_color),
            )
            format_ = "%(message)s"
        else:
            handler = logging.StreamHandler(stream=sys.stderr)
            format_ = "%(levelname)s %(message)s"
        handlers = [handler]
        logging.basicConfig(level=level, format=format_, handlers=handlers)

        return self

    def __exit__(self, exc_type, exc_value, tb):  # pragma: no cover
        if exc_type:
            if exc_type is KeyboardInterrupt:
                self.console.print("[red]Aborted.")
            else:
                self.console.print("[red][bold]Failed.")
            sys.exit(1)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-v", "--verbose", count=True, help="Increase Verbosity.")
@click.option("--no-color", is_flag=True, help="Disable Coloring.", envvar="UCDP_NO_COLOR")
@click.version_option()
@click.pass_context
def cli(ctx, verbose=0, no_color=False):
    """Easy-To-Use SystemVerilog Parser."""
    ctx.obj = ctx.with_resource(Ctx.create(verbose=verbose, no_color=no_color))


pass_ctx = click.make_pass_decorator(Ctx)


@cli.command()
@arg_filepath
@pass_ctx
def gen_sv_instance(ctx, file_path):  # noqa: ARG001
    """Parses an SystemVerilog file and returns a instance of the module."""
    file = parse_file(file_path)

    for module in file.modules:
        instance = gen_instance(module)
        print(instance)


@cli.command()
@arg_filepath
@pass_ctx
@click.option(
    "--width",
    "-w",
    type=int,
    help="Enforce Table Width. Environment Variable SV_SIMPLEPARSER_WIDTH.",
    envvar="SV_SIMPLEPARSER_WIDTH",
)
@click.option("--level", "-l", type=int, default=2, help="Markdown Header Level. Default 2. Means '##'")
@click.option("--sub", "-s", is_flag=True, help="Show Submodules")
def info(ctx: Ctx, file_path: Path, width: int | None = None, level: int = 2, sub: bool = False) -> None:
    """Creates Markdown Overview Tables."""
    file = parse_file(file_path)
    pre = "#" * level
    for module in file.modules:
        params, ports, insts = gen_markdown_table(module, width=width)
        ctx.console.print(f"""\
{pre} Module `{module.name}`

Path `{file.path!s}`
""")

        if params:
            ctx.console.print(f"{pre}# Parameters")
            ctx.console.print(params)

        ctx.console.print(f"{pre}# Ports")
        if ports:
            ctx.console.print(ports)
        else:
            ctx.console.print("\nNo Ports\n")

        if sub:
            ctx.console.print(f"{pre}# Submodules")
            if insts:
                ctx.console.print(insts)
            else:
                ctx.console.print("\nNo Submodules\n")


@cli.command()
@arg_filepath
def json(file_path: Path) -> None:
    """Dump All Extracted Information in a JSON file."""
    file = parse_file(file_path)
    print(file.overview)
