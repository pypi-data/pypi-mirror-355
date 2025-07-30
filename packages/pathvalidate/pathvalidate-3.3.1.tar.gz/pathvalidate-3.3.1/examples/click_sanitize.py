#!/usr/bin/env python3

import click

from pathvalidate.click import sanitize_filename_arg, sanitize_filepath_arg


@click.command()
@click.option("--filename", type=str, callback=sanitize_filename_arg)
@click.option("--filepath", type=str, callback=sanitize_filepath_arg)
def cli(filename: str, filepath: str) -> None:
    if filename:
        click.echo(f"filename: {filename}")
    if filepath:
        click.echo(f"filepath: {filepath}")


if __name__ == "__main__":
    cli()
