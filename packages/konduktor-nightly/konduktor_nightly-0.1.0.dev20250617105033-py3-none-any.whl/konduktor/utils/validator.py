"""This module contains a custom validator for the JSON Schema specification.

The main motivation behind extending the existing JSON Schema validator is to
allow for case-insensitive enum matching since this is currently not supported
by the JSON Schema specification.
"""

import json
import time
from pathlib import Path

import jsonschema
import requests
from colorama import Fore, Style

SCHEMA_VERSION = 'v1.32.0-standalone-strict'
SCHEMA_URL = f'https://raw.githubusercontent.com/yannh/kubernetes-json-schema/master/{SCHEMA_VERSION}/podspec.json'
SCHEMA_CACHE_PATH = Path.home() / '.konduktor/schemas/podspec.json'
CACHE_MAX_AGE_SECONDS = 86400  # 24 hours


def case_insensitive_enum(validator, enums, instance, schema):
    del validator, schema  # Unused.
    if instance.lower() not in [enum.lower() for enum in enums]:
        yield jsonschema.ValidationError(f'{instance!r} is not one of {enums!r}')


SchemaValidator = jsonschema.validators.extend(
    jsonschema.Draft7Validator,
    validators={'case_insensitive_enum': case_insensitive_enum},
)


def get_cached_schema() -> dict:
    # Check if schema file exists and is fresh
    if SCHEMA_CACHE_PATH.exists():
        age = time.time() - SCHEMA_CACHE_PATH.stat().st_mtime
        # if old
        if age < CACHE_MAX_AGE_SECONDS:
            with open(SCHEMA_CACHE_PATH, 'r') as f:
                return json.load(f)

    # Download schema
    resp = requests.get(SCHEMA_URL)
    resp.raise_for_status()

    SCHEMA_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEMA_CACHE_PATH, 'w') as f:
        f.write(resp.text)

    return resp.json()


def validate_pod_spec(pod_spec: dict) -> None:
    schema = get_cached_schema()

    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(pod_spec), key=lambda e: e.path)

    if not errors:
        return

    formatted = [
        f'{Fore.RED}- {error.message}'
        + (f" at path: {' → '.join(str(p) for p in error.path)}" if error.path else '')
        + Style.RESET_ALL
        for error in errors
    ]

    raise ValueError(
        f'\n{Fore.RED}Invalid k8s pod spec/config: \
        {Style.RESET_ALL}\n'
        + '\n'.join(formatted)
    )
