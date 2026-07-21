import click

from interfaceTools.validate_definitions import main as validate


@click.group()
def main():
    """Command line interface for IMAS Standard Interfaces."""


main.add_command(validate, name="validate")


if __name__ == "__main__":
    main()
