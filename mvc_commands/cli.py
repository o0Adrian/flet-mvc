import os
import shutil
import click
from pathlib import Path


def _copy_template_files(template_path_str):
    library_path = Path(__file__).parent
    template_path = library_path / template_path_str

    if not template_path.exists():
        print(
            "Error: The 'templates' directory is missing. Please check that the library is properly installed and has not been modified."
        )
        return

    pwd = Path.cwd()

    for item in template_path.iterdir():
        if item.is_file():
            shutil.copy(item, pwd)
        elif item.is_dir():
            shutil.copytree(item, pwd / item.name)

    print(f"Templates have been copied into {pwd}")


@click.command()
def start():
    """Creates a basic Flet-MVC template."""
    _copy_template_files("templates/basic")


@click.command()
def routes():
    """Creates Flet-MVC template for a routed app."""
    _copy_template_files("templates/routes")
    
@click.command()
def tabs():
    """Creates Flet-MVC template for an app with tabs."""
    _copy_template_files("templates/tabs")


@click.group()
def cli():
    pass


cli.add_command(start)
cli.add_command(routes)
cli.add_command(tabs)



if __name__ == "__main__":
    cli()
