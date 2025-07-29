""" Contains code for Python CLI """

import glob
import os
from typing import Any, Callable, Optional

import click

from scanner_client import Scanner
from scanner_client.detection_rule_yaml import validate_and_read_file

import src.migrate.elastic as elastic_cmd
import src.sync as sync_cmd
from src.utils import format_exception_message

_DEFAULT_CLICK_OPTIONS = [
    click.option(
        "--api-url",
        envvar="SCANNER_API_URL",
        help="The API URL of your Scanner instance. Go to Settings > API Keys in Scanner to find your API URL.",
    ),
    click.option(
        "--api-key",
        envvar="SCANNER_API_KEY",
        help="Scanner API key. Go to Settings > API Keys in Scanner to find your API keys or to create a new API key.",
    ),
    click.option(
        "-f",
        "--file",
        "file_paths",
        help="Detection rule file. This must be .yml or .yaml file with the correct schema header.",
        multiple=True,
    ),
    click.option(
        "-d",
        "--dir",
        "directories",
        help="Directory of detection rule files. Only .yml or .yaml files with the correct schema header will be processed.",
        multiple=True,
    ),
    click.option(
        "-r",
        "recursive",
        is_flag=True,
        show_default=True,
        default=False,
        help="Recursively search directory for valid YAML files.",
    ),
]


def _default_click_options(func) -> Callable[..., Any]:
    for option in reversed(_DEFAULT_CLICK_OPTIONS):
        func = option(func)

    return func


def _is_valid_file(file_path: str) -> bool:
    try:
        validate_and_read_file(file_path)
        return True
    except:
        return False


def _get_valid_files_in_directory(directory: str, recursive: bool) -> list[str]:
    if not os.path.exists(directory):
        raise click.exceptions.ClickException(
            message=(
                f"Directory {directory} not found."
            )
        )

    return [f for f in glob.iglob(f"{directory}/**", recursive=recursive) if _is_valid_file(f)]


def _get_valid_files(file_paths: str, directories: str, recursive: bool) -> list[str]:
    files = [f for f in file_paths if _is_valid_file(f)]

    for d in directories:
        files.extend(_get_valid_files_in_directory(d, recursive))

    return files


def _validate_default_options(api_url: str, api_key: str, file_paths: str, directories: str) -> None:
    if api_url is None:
        raise click.exceptions.UsageError(
            message=(
                "Pass --api-url option or set `SCANNER_API_URL` environment variable."
            )
        )

    if api_key is None:
        raise click.exceptions.UsageError(
            message=(
                "Pass --api-key option or set `SCANNER_API_KEY` environment variable."
            )
        )

    if not file_paths and not directories:
        raise click.exceptions.UsageError(
            message=(
                "Either --file or --dir must be provided."
            )
        )


@click.group()
def cli():
    """ Python CLI for Scanner API """


@cli.command()
@_default_click_options
def validate(api_url: str, api_key: str, file_paths: str, directories: str, recursive: bool):
    """ Validate detection rule files """
    _validate_default_options(api_url, api_key, file_paths, directories)

    scanner_client = Scanner(api_url, api_key)

    files = _get_valid_files(file_paths, directories, recursive)
    click.echo(f'Validating {len(files)} {"file" if len(files) == 1 else "files"}')

    any_failures: bool = False

    for file in files:
        try:
            result = scanner_client.detection_rule_yaml.validate(file)

            if result.is_valid:
                if result.warning:
                    click.echo(f"{file}: " + click.style("OK. ", fg="green") + click.style(f"Warning: {result.warning}", fg="yellow"))
                else:
                    click.echo(f"{file}: " + click.style("OK", fg="green"))
            else:
                any_failures = True
                click.echo(f"{file}: " + click.style(f"{result.error}", fg="red"))
        except Exception as e:
            any_failures = True
            error_msg = format_exception_message(e, "An exception occurred when attempting to validate file")
            click.echo(f"{file}: " + click.style(error_msg, fg="red"))

    if any_failures:
        # To make it so the CLI exits with a non-zero exit code
        raise click.ClickException(
            "`validate` failed for one or more files. See https://docs.scanner.dev/scanner/using-scanner/beta-features/detection-rules-as-code/writing-detection-rules for requirements."
        )
    else:
        click.secho("All specified detection rule files are valid. Use `run-tests` to run the detection rule tests.", bold=True)


@cli.command()
@_default_click_options
def run_tests(api_url: str, api_key: str, file_paths: str, directories: str, recursive: bool):
    """ Run detection rule tests """
    _validate_default_options(api_url, api_key, file_paths, directories)

    scanner_client = Scanner(api_url, api_key)

    files = _get_valid_files(file_paths, directories, recursive)
    click.echo(f'Running tests on {len(files)} {"file" if len(files) == 1 else "files"}')

    any_validation_errors: bool = False
    any_test_failures: bool = False

    for file in files:
        click.secho(f"{file}", bold=True)
        try:
            # Check for validation errors
            validation_result = scanner_client.detection_rule_yaml.validate(file)
            if not validation_result.is_valid:
                any_validation_errors = True
                click.secho(f"Validation error: {validation_result.error}", fg="red")
                click.echo("")
                continue

            if validation_result.warning:
                click.secho(f"Warning: {validation_result.warning}", fg="yellow")

            # Run detection rule tests
            run_tests_response = scanner_client.detection_rule_yaml.run_tests(file)
            results = run_tests_response.results.to_dict()

            if len(results) == 0:
                click.secho("No tests found", fg="yellow")
            else:
                for name, status in results.items():
                    if status == "Passed":
                        click.echo(f"{name}: " + click.style("OK", fg="green"))
                    else:
                        any_test_failures = True
                        click.echo(f"{name}: " + click.style("Test failed", fg="red"))
        except Exception as e:
            any_test_failures = True
            error_msg = format_exception_message(e, "An exception occurred when attempting to run tests")
            click.secho(error_msg, fg="red")

        click.echo("")

    error_messages = []
    if any_validation_errors:
        error_messages.append("Validation failed for one or more files. See https://docs.scanner.dev/scanner/using-scanner/beta-features/detection-rules-as-code/writing-detection-rules for requirements.")

    if any_test_failures:
        error_messages.append("`run-tests` failed for one or more files. See https://docs.scanner.dev/scanner/using-scanner/beta-features/detection-rules-as-code/cli#failing-tests for more information.")

    if error_messages:
        # To make it so the CLI exits with a non-zero exit code
        raise click.ClickException("\n".join(error_messages))


@cli.command()
@_default_click_options
@click.option(
    "--team-id",
    envvar="SCANNER_TEAM_ID",
    help="The team ID to which you want to sync the Scanner rules. Go to Settings > General to find the Team ID.",
    required=True,
)
@click.option(
    "--sync-config-file",
    help="Optional. The path to the sync configuration file the CLI will use to sync detection rules to Scanner. (eg. contains event_sink_keys mappings, etc).",
    required=False,
)
def sync(
    api_url: str,
    api_key: str,
    file_paths: str,
    directories: str,
    recursive: bool,
    team_id: str,
    sync_config_file: Optional[str]
):
    """ Sync detection rules to Scanner """
    _validate_default_options(api_url, api_key, file_paths, directories)
    if team_id is None:
        raise click.exceptions.UsageError(
            message=(
                "Pass --team-id option or set `SCANNER_TEAM_ID` environment variable."
            )
        )

    scanner_client: Scanner = Scanner(api_url, api_key)
    files: list[str] = _get_valid_files(file_paths, directories, recursive)
    # Note: In the Scanner UI, the tenant_id is called Team ID.
    sync_cmd.sync(scanner_client, files, team_id, sync_config_file)


@cli.command()
@click.option(
    "-c",
    "--migrate-config-file",
    help="Optional. The path to the migration configuration file the CLI will use to migrate Elastic rules (eg. contains data_view_id_to_query_term mappings, etc).",
)
@click.option(
    "-f",
    "--elastic-rules-file",
    help="The path to the Elastic detection rules ndjson file the CLI will migrate.",
    required=True,
)
@click.option(
    "-o",
    "--output-dir",
    help="The directory where the migrated rules will be saved. Will create one YAML file per rule.",
    required=True,
)
def migrate_elastic_rules(migrate_config_file: Optional[str], elastic_rules_file: str, output_dir: str):
    """ Migrate Elastic SIEM rules to Scanner rules """
    elastic_cmd.migrate_elastic_rules(migrate_config_file, elastic_rules_file, output_dir)


if __name__ == "__main__":
    cli()
