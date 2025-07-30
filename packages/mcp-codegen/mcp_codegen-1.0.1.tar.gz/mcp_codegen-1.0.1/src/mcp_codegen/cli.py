# cli.py
import click
from mcp_codegen import mcp_proj_codegen


@click.command()
def create_mcp_project_structure():
    mcp_proj_codegen.main()


if __name__ == "__main__":
    create_mcp_project_structure()
