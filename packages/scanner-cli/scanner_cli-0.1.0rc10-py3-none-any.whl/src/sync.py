from dataclasses import dataclass
from typing import Any, Optional
import typing

import click
import yaml
import sys

from scanner_client import Scanner, NotFound
from scanner_client.detection_rule import string_to_detection_severity, DetectionSeverity
from scanner_client.detection_rule_yaml import validate_and_read_file


@dataclass
class DetectionRuleConfig:
   file: str
   detection_rule: dict[str, Any]
   event_sink_ids: list[str]


def _get_detection_rule_id_for_sync_key(
    scanner_client: Scanner,
    sync_key: str,
) -> Optional[str]:
    try:
        detection_rule = scanner_client.detection_rule.get_by_sync_key(sync_key)
        return detection_rule.id
    except NotFound:
        return None


def _read_sync_config_from_file(sync_config_file: str) -> dict[str, Any]:
    with open(sync_config_file, 'r') as f:
        contents = f.read()
        any_sync_config: Any = yaml.safe_load(contents)
        if not isinstance(any_sync_config, dict):
            raise click.exceptions.UsageError(
                message=(
                    "sync_config_file must be a YAML file with a dictionary at the root"
                )
            )
        sync_config: dict[str, Any] = any_sync_config
        return sync_config


def _get_event_sink_ids(detection_rule: dict[str, Any], sync_config: dict[str, Any]) -> list[str]:
    event_sink_ids: list[str] = []
    detection_rule_event_sink_keys = detection_rule.get('event_sink_keys', [])
    sync_config_event_sink_keys = sync_config.get('event_sink_keys', {})
    if not isinstance(sync_config_event_sink_keys, dict):
        raise click.exceptions.UsageError(
            message=(
                "Please supply a sync-config-file where event_sink_keys is present"
            )
        )
    for event_sink_key in detection_rule_event_sink_keys:
        mapped_event_sinks = sync_config_event_sink_keys.get(event_sink_key)
        if not isinstance(mapped_event_sinks, list):
            raise click.exceptions.UsageError(
                message=(
                    f"Please supply a sync-config-file where {event_sink_key} is present under event_sink_keys."
                )
            )
        for mapped_event_sink in mapped_event_sinks:
            if not isinstance(mapped_event_sink, dict):
                raise click.exceptions.UsageError(
                    message=(
                        f"Event sink key {event_sink_key} must be a list of dictionaries in sync config file."
                    )
                )
            event_sink_id = mapped_event_sink.get('sink_id')
            if not event_sink_id:
                raise click.exceptions.UsageError(
                    message=(
                        f"Event sink key {event_sink_key} must have a sink_id in sync config file."
                    )
                )
            event_sink_ids.append(event_sink_id)
    return event_sink_ids


def sync(scanner_client: Scanner, files: list[str], tenant_id: str, sync_config_file: Optional[str]):
    click.echo(f'Syncing {len(files)} detection rule {"file" if len(files) == 1 else "files"} to Scanner Team {tenant_id}')

    any_failures: bool = False

    sync_config: dict[str, Any] = {}
    if sync_config_file:
        sync_config = _read_sync_config_from_file(sync_config_file)

    click.echo("Validating rules before syncing...")
    detection_rule_configs: list[DetectionRuleConfig] = []
    for file in files:
        try:
            result = scanner_client.detection_rule_yaml.validate(file)

            if result.is_valid:
                click.echo(f"{file}: " + click.style("Valid", fg="green"))
            else:
                any_failures = True
                click.echo(f"{file}: " + click.style(f"{result.error}", fg="red"))
                continue

            contents: str = validate_and_read_file(file)
            detection_rule: dict[str, Any] = yaml.safe_load(contents)

            if not detection_rule.get('sync_key'):
                any_failures = True
                click.secho(f"Error: sync_key not found in {file}", fg="red")
                continue

            # Will raise an exception if the event sink keys are not valid
            event_sink_ids: list[str] = _get_event_sink_ids(detection_rule, sync_config)

            detection_rule_configs.append(DetectionRuleConfig(
                file=file,
                detection_rule=detection_rule,
                event_sink_ids=event_sink_ids,
            ))
        except Exception as e:
            any_failures = True
            click.echo(f"{file}: " + click.style(e, fg="red"))

    if any_failures:
        # To make it so the CLI exits with a non-zero exit code
        raise click.ClickException(
            "validate failed for one or more files. Sync aborted."
        )

    click.secho("All rules are valid", fg="green")
    click.echo("")

    click.echo("Syncing rules to Scanner...")
    num_created: int = 0
    num_updated: int = 0
    for detection_rule_config in detection_rule_configs:
        file = detection_rule_config.file
        detection_rule = detection_rule_config.detection_rule
        event_sink_ids = detection_rule_config.event_sink_ids

        try:
            # At this point, we know sync_key is present
            sync_key: str = detection_rule['sync_key']
            detection_rule_id: Optional[str] = _get_detection_rule_id_for_sync_key(
                scanner_client,
                sync_key,
            )

            severity: DetectionSeverity = string_to_detection_severity(
                detection_rule['severity']
            )

            if detection_rule_id:
                scanner_client.detection_rule.update(
                    sync_key=sync_key,
                    detection_rule_id=detection_rule_id,
                    name=detection_rule['name'],
                    description=detection_rule['description'],
                    time_range_s=detection_rule['time_range_s'],
                    run_frequency_s=detection_rule['run_frequency_s'],
                    enabled=detection_rule['enabled'],
                    severity=severity,
                    query_text=detection_rule['query_text'],
                    event_sink_ids=event_sink_ids,
                )
                click.echo(f"{sync_key}: " + click.style("Updated", fg="green"))
                num_updated += 1
            else:
                scanner_client.detection_rule.create(
                    sync_key=detection_rule['sync_key'],
                    tenant_id=tenant_id,
                    name=detection_rule['name'],
                    description=detection_rule['description'],
                    time_range_s=detection_rule['time_range_s'],
                    run_frequency_s=detection_rule['run_frequency_s'],
                    enabled=detection_rule['enabled'],
                    severity=severity,
                    query_text=detection_rule['query_text'],
                    event_sink_ids=event_sink_ids,
                )
                click.echo(f"{sync_key}: " + click.style("Created", fg="green"))
                num_created += 1
        except Exception as e:
            any_failures = True
            click.echo(click.style("Failed to sync file", fg="red") + f": {file}")
            click.echo(click.style("Error", fg="red") + f": {e}")
            click.echo("")
            break

    if any_failures:
        # To make it so the CLI exits with a non-zero exit code
        raise click.ClickException(
            "sync failed for one or more files"
        )

    if num_created > 0:
        click.secho(f"Created {num_created} rule(s)", fg="green")
    if num_updated > 0:
        click.secho(f"Updated {num_updated} rule(s)", fg="green")
