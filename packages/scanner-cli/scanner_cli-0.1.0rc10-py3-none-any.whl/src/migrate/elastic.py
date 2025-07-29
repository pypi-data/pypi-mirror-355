import json
import os
from typing import Any, Optional

import click
import yaml
from yaml import Dumper


class YamlStrLiteral(str):
    """
    A class to represent a YAML literal string, which may have multiple lines.
    Helps us to represent a string as a literal block scalar in YAML.
    """
    pass


def _represent_literal(dumper: Dumper, data: YamlStrLiteral) -> Any:
    return dumper.represent_scalar(
            yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
            data,
            style="|"
    )


yaml.add_representer(YamlStrLiteral, _represent_literal)


def _validate_options(migrate_config_file: Optional[str], elastic_rules_file: str, output_dir: str):
    if migrate_config_file and not os.path.exists(migrate_config_file):
        raise click.exceptions.UsageError(
            message=(
                "Config file not found."
            )
        )
    if not os.path.exists(elastic_rules_file):
        raise click.exceptions.UsageError(
            message=(
                "Elastic rules file not found."
            )
        )
    if not os.path.isdir(output_dir):
        raise click.exceptions.UsageError(
            message=(
                "Output directory not found."
            )
        )


def _migrate_to_scanner_yml(elastic_detection_rule: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    name: str = elastic_detection_rule.get('name', '')
    description: YamlStrLiteral = YamlStrLiteral(elastic_detection_rule.get('note', ''))
    enabled: bool = elastic_detection_rule.get('enabled', True)
    severity: str = _capitalize_first_letter(elastic_detection_rule.get('severity', 'unknown'))
    query_text: YamlStrLiteral = YamlStrLiteral(_get_query_text_for_detection_rule(elastic_detection_rule, config))
    time_range_s: int = 300
    run_frequency_s: int = 60
    event_sink_key: str = _migrate_severity_to_event_sink_key(severity)
    file_name: str = _generate_rule_file_name(name)
    scanner_rule: dict[str, Any] = {
        'sync_key': file_name,
        'name': name,
        'description': description,
        'enabled': enabled,
        'severity': severity,
        'query_text': query_text,
        'time_range_s': time_range_s,
        'run_frequency_s': run_frequency_s,
        'event_sink_keys': [event_sink_key],
    }
    yaml_content: str = yaml.dump(
        scanner_rule,
        default_flow_style=False,
        sort_keys=False
    )
    yaml_content = yaml_content.replace('\\', '\\\\')
    yaml_content = "# schema: https://scanner.dev/schema/scanner-detection-rule.v1.json\n" + yaml_content
    return {
        'file_name': file_name,
        'yaml_content': yaml_content,
    }


def _generate_rule_file_name(name: str) -> str:
    chars = []
    for c in name:
        if c.isalnum():
            chars.append(c.lower())
        elif chars and chars[-1] != ' ':
            chars.append(' ')
    file_name = ''.join(chars)
    file_name = file_name.strip()
    file_name = file_name.replace(' ', '_')
    return f"{file_name}.yml"


def _migrate_severity_to_event_sink_key(severity: str) -> str:
    return f"{severity.lower()}_severity_alerts"


def _capitalize_first_letter(text: str) -> str:
    if text:
        return text[0].upper() + text[1:]
    return text


def _get_query_text_for_detection_rule(elastic_detection_rule: dict[str, Any], config: dict[str, Any]) -> str:
    query_parts: list[str] = []
    data_view_id: Optional[str] = elastic_detection_rule.get('data_view_id')
    data_view_id_query_term: Optional[str] = config.get('data_view_id_to_query_term', {}).get(data_view_id)
    if data_view_id_query_term:
        query_parts.append(data_view_id_query_term)
    main_query: Optional[str] = elastic_detection_rule.get('query')
    if main_query:
        query_parts.append(main_query)
    filters: list[dict[str, Any]] = elastic_detection_rule.get('filters', [])
    for filter in filters:
        query_text = _get_query_text_for_filter(filter)
        if query_text:
            query_parts.append(query_text)
    return "\n".join(query_parts)


def _get_query_text_for_filter(f: dict[str, Any]) -> Optional[str]:
    should_negate: bool = f.get('meta', {}).get('negate', False)
    filter_query: dict[str, Any] = f.get('query', {})
    query_text: Optional[str] = _get_query_text_for_filter_query(filter_query)
    if query_text is None:
        return None
    if should_negate:
        query_text = f"not {query_text}"
    return query_text


def _get_query_text_for_filter_query(filter_query: dict[str, Any]) -> Optional[str]:
    match_phrase_query: Optional[dict[str, Any]] = filter_query.get('match_phrase')
    bool_query: Optional[dict[str, Any]] = filter_query.get('bool')
    exists_query: Optional[dict[str, Any]] = filter_query.get('exists')
    if match_phrase_query:
        return _get_query_text_for_match_phrase_query(match_phrase_query)
    elif bool_query:
        return _get_query_text_for_bool_query(bool_query)
    elif exists_query:
        return _get_query_text_for_exists_query(exists_query)
    return None


def _get_query_text_for_match_phrase_query(match_phrase_query: dict[str, Any]) -> str:
    query_parts: list[str] = []
    for field, value in match_phrase_query.items():
        query_parts.append(f"{field}: \"{value}\"")
    has_multiple_parts: bool = len(query_parts) > 1
    query_text: str = "\n".join(query_parts)
    if has_multiple_parts:
        return f"({query_text})"
    else:
        return query_text


def _get_query_text_for_bool_query(bool_query: dict[str, Any]) -> Optional[str]:
    minimum_should_match: Optional[int] = bool_query.get('minimum_should_match')
    if minimum_should_match != 1:
        # Print error message that this is unsupported
        click.secho("Unsupported filter: Only support bool minimum_should_match = 1", fg="red")
        return None
    query_parts: list[str] = []
    should_clauses: list[dict[str, Any]] = bool_query.get('should', [])
    for should_clause in should_clauses:
        query_text: Optional[str] = _get_query_text_for_filter_query(should_clause)
        if query_text is None:
            return None
        query_parts.append(query_text)
    has_multiple_parts: bool = len(query_parts) > 1
    returned_query_text: str = " or ".join(query_parts)
    if has_multiple_parts:
        return f"({returned_query_text})"
    else:
        return returned_query_text


def _get_query_text_for_exists_query(exists_query: dict[str, Any]) -> Optional[str]:
    field: Optional[str] = exists_query.get('field')
    if field:
        return f"{field}: *"
    else:
        return None


def migrate_elastic_rules(migrate_config_file: Optional[str], elastic_rules_file: str, output_dir: str):
    _validate_options(migrate_config_file, elastic_rules_file, output_dir)

    any_failures: bool = False

    count: int = 0
    try:
        config: dict[str, Any] = {}
        if migrate_config_file:
            with open(migrate_config_file, 'r') as file:
                config = yaml.safe_load(file)
        with open(elastic_rules_file, 'r') as file:
            for raw_line in file:
                line: str = raw_line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    elastic_detection_rule: dict[str, Any] = json.loads(line)
                    migrated: dict[str, Any] = _migrate_to_scanner_yml(elastic_detection_rule, config)
                    output_file_path: str = f"{output_dir}/{migrated['file_name']}"
                    with open(output_file_path, 'w') as output_file:
                        output_file.write(migrated['yaml_content'])
                    count += 1
                    click.echo(click.style("Migrated", fg="green") + f": {output_file_path}")
                except json.JSONDecodeError as e:
                    click.secho(f"Error parsing JSON on line: {line}", fg="red")
                    click.secho(f"Error details: {e}", fg="red")
                    click.echo("")
                    any_failures = True
                    continue
    except yaml.YAMLError as e:
        any_failures = True
        click.secho(f"YAML Error: {e}", fg="red")
        click.echo("")
    except BaseException as e:
        any_failures = True
        click.secho(f"Error: {e}", fg="red")
        click.echo("")

    click.secho(f"Successfully migrated {count} rules", fg="green")
    click.echo(click.style("Output directory", fg="green") + f": {output_dir}")

    if any_failures:
        # To make it so the CLI exits with a non-zero exit code
        raise click.ClickException(
            "migrate-elastic-rules failed for one or more rules"
        )
