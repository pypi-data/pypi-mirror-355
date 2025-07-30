#!/usr/bin/env python3

import re

from hardcoded.logic import File, _debug

import yaml
import click


@click.command()
@click.option(
    "--encrypt",
    is_flag=True,
    help="Write the data file encrypted, regardless of its previous status.",
)
@click.option(
    "--decrypt",
    is_flag=True,
    help="Write the data file in plain text, regardless of its previous status.",
)
@click.option("--file", help=f"The file to work on. [{File()._x.path}]")
# @click.option('--import-file', help=f'A file to import as key-values into {File()._x.path}.')
@click.option("--where", is_flag=True, help="Show which file is used.")
@click.option("-d", "--debug", is_flag=True, help="Turn on debug output.")
@click.argument("key", required=False)
def cli(key, encrypt, decrypt, file, where, debug):
    if debug:
        _debug.enabled = True
    if encrypt and decrypt:
        raise ValueError("Please choose one of --encrypt and --decrypt.")
    elif encrypt or decrypt:
        secret = encrypt
    else:
        secret = None
    datafile = File(secret=secret, path=file)

    if where:
        # TODO: If / when we implement hierarchical overlay files, show info about what is read from / written to which file.
        click.echo(File()._x.path)
        exit()

    # TODO: Allow to import from other simple YAML, two-column CSV, INI and .env files.
    # if import_file:
    #    click.echo('boo')
    #    exit()

    if key:
        click.echo(datafile.get(key), err=False, nl=False)
    else:
        stdin_text = click.get_text_stream("stdin")
        if stdin_text.isatty():
            # Interactive session: open datafile in an editor.
            data = datafile._x._get_all_decrypted_data()
            data_yaml = yaml.safe_dump(data)
            edited_data_yaml = data_yaml
            while True:
                edited_data_yaml = click.edit(edited_data_yaml)
                try:
                    if edited_data_yaml is None:
                        click.echo("Data not changed.", err=True)
                    else:
                        # Let's fail here if the user messed up the YAML.
                        edited_data = yaml.safe_load(edited_data_yaml)
                        datafile._x._set_all_data(edited_data)
                        click.echo(f"{datafile._x.path} updated.", err=True)
                    break
                except yaml.YAMLError as ex:
                    if hasattr(ex, "problem_mark"):
                        mark = ex.problem_mark
                        click.echo(
                            f"Error in {datafile._x.path} YAML at {mark.line + 1}:{mark.column + 1}: {ex}",
                            err=True,
                        )
                    else:
                        click.echo(f"Error in {datafile._x.path} YAML: {ex}", err=True)
                    if not click.confirm(
                        "Do you want to try again?", default=True, err=True
                    ):
                        break
        else:
            # Non-interactive session: replace hardcoded patterns in stdin, send to stdout.
            text = stdin_text.read()
            text = re.sub(
                r'hardcoded[\.\(\'"]+([\w\d]+)[\'"]?\)?',
                lambda match: datafile.get(match.group(1)),
                text,
            )
            click.echo(text, err=False, nl=False)


if __name__ == "__main__":
    cli()
