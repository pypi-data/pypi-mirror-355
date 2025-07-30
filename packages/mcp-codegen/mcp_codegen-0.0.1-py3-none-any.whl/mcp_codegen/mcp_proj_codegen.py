"""MIT License

Copyright (c) 2025 Biprajeet Kar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


from __future__ import annotations

import pathlib
import re
import sys
import textwrap
from typing import Any, Dict, List

import yaml

# --------------------------------------------------------------------------- #
# Locate YAML spec                                                            #
# --------------------------------------------------------------------------- #

SPEC_FILE = pathlib.Path.cwd() / "mcp_cfg.yaml"
if not SPEC_FILE.exists():
    sys.exit("❌  mcp_cfg.yaml not found in the current directory.")

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def to_snake(text: str) -> str:
    """Convert arbitrary text to snake_case."""
    return re.sub(r"[\W|_]+", "_", text).lower()


def indent_block(block: str, spaces: int = 8) -> str:
    """Indent every line in *block* by *spaces* spaces."""
    return textwrap.indent(block, " " * spaces)


TEMPLATE_TOOL = textwrap.dedent(
    """\
\"\"\"Auto-generated tool module.\"\"\"

from typing import Any

def {func_name}({signature}) -> Any:
    \"\"\"
    {description}

    Parameters
    ----------
{param_lines}

    Returns
    -------
    Any
        Result of the tool.
    \"\"\"
    # TODO: implement tool logic
    raise NotImplementedError
"""
)


def build_tool_code(tool: Dict[str, Any]) -> str:
    """Render a Python module for a single tool entry."""
    params: List[str] = []
    param_docs: List[str] = []

    for arg in tool.get("tool_args", []):
        name = to_snake(arg["arg_variable"])
        a_type = arg["arg_type"]
        default = (
            f"={arg['default_value']}"
            if str(arg.get("optional", "N")).upper() == "Y"
            else ""
        )

        params.append(f"{name}: {a_type}{default}")
        param_docs.append(f"{name} ({a_type}): {arg['arg_description']}")

    signature = ", ".join(params)
    doc_param_block = "\n".join(param_docs) if param_docs else "None"
    param_lines = indent_block(doc_param_block, 8)  # aligns under docstring body

    return TEMPLATE_TOOL.format(
        func_name=to_snake(tool["tool_name"]),
        signature=signature,
        description=tool["tool_description"],
        param_lines=param_lines,
    )


# --------------------------------------------------------------------------- #
# Main                                                                        #
# --------------------------------------------------------------------------- #


def main() -> None:
    out_dir = (
        pathlib.Path(sys.argv[1]).resolve()
        if len(sys.argv) > 1
        else pathlib.Path.cwd()
    )

    with SPEC_FILE.open("r", encoding="utf-8") as fh:
        spec = yaml.safe_load(fh)

    tools_dir = out_dir / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "__init__.py").touch()

    imports: List[str] = []
    registers: List[str] = []

    # --------------------------------------------------------------------- #
    # Generate or keep each tool module                                     #
    # --------------------------------------------------------------------- #
    for tool in spec["mcp_server"]["mcp_tools"]:
        module_name = f"{to_snake(tool['tool_name'])}_tool"
        func_name = to_snake(tool["tool_name"])
        tool_path = tools_dir / f"{module_name}.py"

        if tool_path.exists():
            print(f"•  {tool_path.name} already exists – keeping user edits.")
        else:
            tool_path.write_text(build_tool_code(tool), encoding="utf-8")

        imports.append(f"from tools.{module_name} import {func_name}")
        registers.append(f"mcp.add_tool({func_name})")

    # --------------------------------------------------------------------- #
    # Build mcp_server.py                                                   #
    # --------------------------------------------------------------------- #
    imports_block = "\n".join(imports)
    registers_block = "\n".join(registers)
    transport_mode = spec["mcp_server"].get("mcp_transport_mode", "stdio")

    server_code = textwrap.dedent(
        f"""\
        \"\"\"Auto-generated FastMCP server.\"\"\"

        {imports_block}
        from mcp.server.fastmcp import FastMCP

        mcp = FastMCP("Demo")

        {registers_block}

        if __name__ == "__main__":
            mcp.run(transport="{transport_mode}")
        """
    )
    (out_dir / "mcp_server.py").write_text(server_code, encoding="utf-8")

    # --------------------------------------------------------------------- #
    # requirements.txt                                                      #
    # --------------------------------------------------------------------- #
    (out_dir / "requirements.txt").write_text(
        "mcp\npyyaml\n", encoding="utf-8"
    )

    print(f"✔  Project generated in {out_dir} using {SPEC_FILE.name}")


if __name__ == "__main__":
    main()
