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

from importlib.resources import files

from jinja2 import Environment, FileSystemLoader
from rich.table import Table, box

from .datamodel import Module

template_path = files("sv_simpleparser.Templates")


def gen_instance(mod):
    port_lst = [port.name for port in mod.ports]
    param_lst = [param.name for param in mod.params]

    environment = Environment(loader=FileSystemLoader(template_path))

    if param_lst:
        inst_temp = environment.get_template("instance_with_param_template")

        instance_file = inst_temp.render(module_name=mod.name, param_list=param_lst, port_list=port_lst)
    else:
        inst_temp = environment.get_template("instance_template")

        instance_file = inst_temp.render(module_name=mod.name, port_list=port_lst)

    return instance_file


def gen_markdown_table(mod: Module) -> tuple[Table, Table]:
    table = Table(title=f"`{mod.name}` Interface", box=box.MARKDOWN)

    table.add_column("Name", no_wrap=True)
    table.add_column("Dimension", no_wrap=True)
    table.add_column("I/O", no_wrap=True)
    table.add_column("Functional Description")

    table_param = Table(title=f"`{mod.name}` Parameters", box=box.MARKDOWN)

    table_param.add_column("Name", no_wrap=True)
    table_param.add_column("Dimension", no_wrap=True)
    table_param.add_column("Functional Description")

    for port in mod.ports:
        dim = port.dim or "1"
        port_name = f"{port.name} {port.dim_unpacked}" if port.dim_unpacked else port.name
        table.add_row(f"`{port_name}`", f"`{dim}`", f"`{port.direction}`", "\n".join(port.comment or ()))

    for param in mod.params:
        param_name = f"{param.name} {param.dim_unpacked}" if param.dim_unpacked else param.name
        dim = f"`{param.dim}`" if param.dim else ""
        table_param.add_row(f"`{param_name}`", dim, "\n".join(param.comment or ()))

    return table, table_param
