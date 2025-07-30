"""Misc functions."""

import abc
import hashlib
import secrets
import string
from typing import Any, Awaitable, Callable, Iterable

import lorem_pysum
from jsonrpcobjects.objects import ParamsRequest, Request, ResultResponse
from openrpc import Example, Method, ParamStructure, SchemaType

RequestProcessor = Callable[[str, dict[str, Any]], Awaitable[str | None]]


class OAuthChallengeHandler(abc.ABC):
    """Determine behavior for creating and getting OAuth verifiers."""

    @abc.abstractmethod
    def create_verifier(self) -> str:
        """Create a challenge to be used by OAuth and return the hash."""

    @abc.abstractmethod
    def get_verifier(self, challenge: str) -> str | None:
        """Get a verifier from a challenge."""


class DefaultHandler(OAuthChallengeHandler):
    def __init__(self) -> None:
        self._challenges: dict[str, str] = {}
        self._challenge_length = 128

    def get_verifier(self, challenge: str) -> str | None:
        return self._challenges.get(challenge)

    def create_verifier(self) -> str:
        characters = string.ascii_letters + string.digits
        challenge = "".join(
            secrets.choice(characters) for _ in range(self._challenge_length)
        )
        sha256_hash = hashlib.sha256(challenge.encode()).hexdigest()
        self._challenges[sha256_hash] = challenge
        return sha256_hash


def get_schema_from_input_ids(
    schema: SchemaType, input_ids: Iterable[int]
) -> SchemaType:
    """Get the appropriate schema from input ids."""
    for id_ in input_ids:
        schema = _get_schema_from_input_id(schema, id_)
    return schema


def _get_schema_from_input_id(schema: SchemaType, input_id: int) -> SchemaType:
    """Get the appropriate schema from an input id."""
    if isinstance(schema, bool):
        return schema
    if schema.items:
        return schema.items
    if schema.additional_properties:
        return schema.additional_properties
    if schema.any_of:
        return schema.any_of[input_id]
    if schema.properties:
        return list(schema.properties.values())[input_id]
    return schema


def get_examples(methods: list[Method]) -> dict[str, tuple[str, str]]:
    """Get request/response examples for each method with examples.

    The keys in the returned dictionary will be method names, the values
    will be a tuple of (request example, response example).
    """
    examples: dict[str, tuple[str, str]] = {}
    for method in methods:
        if not method.examples:
            continue
        param_example = method.examples[0].params
        result_example = method.examples[0].result
        if param_example is None or result_example is None:
            continue
        examples[method.name] = (
            _get_example_request(method.name, param_example, method.param_structure),
            _get_example_response(result_example),
        )
    return examples


def _get_example_request(
    method: str, examples: list[Example], param_structure: ParamStructure | None
) -> str:
    """Get an example request."""
    if param_structure is ParamStructure.BY_POSITION or not all(
        e.name for e in examples
    ):
        example_params: list[Any] | dict[str | None, Any] = [e.value for e in examples]
    else:
        example_params = {e.name: e.value for e in examples}
    if example_params:
        request: Request | ParamsRequest = lorem_pysum.generate(
            ParamsRequest, overrides={"method": method, "params": example_params}
        )
    else:
        request = lorem_pysum.generate(Request, overrides={"method": method})
    return request.model_dump_json(indent=2, by_alias=True)


def _get_example_response(example: Example) -> str:
    """Get an example request."""
    return lorem_pysum.generate(
        ResultResponse, overrides={"result": example.value}
    ).model_dump_json(indent=2, by_alias=True)


def is_any(schema: SchemaType | None) -> bool:
    """Return true if the given schema is any."""
    if schema is None or schema is True:
        return True
    return schema is False or not any(
        (
            "type" in schema.model_fields_set,
            "ref" in schema.model_fields_set,
            "all_of" in schema.model_fields_set,
            "any_of" in schema.model_fields_set,
            "one_of" in schema.model_fields_set,
            "const" in schema.model_fields_set,
            "enum" in schema.model_fields_set,
            "not_" in schema.model_fields_set,
        )
    )


def get_any_default(schema: SchemaType) -> int:
    """Get default option of an `anyOf` schema."""
    default = 0
    if isinstance(schema, bool):
        return default
    for i, any_schema in enumerate(schema.any_of or []):
        if isinstance(any_schema, bool):
            continue
        if "default" in schema.model_fields_set and (
            (
                "const" in any_schema.model_fields_set
                and schema.default == any_schema.const
            )
            or (schema.default is None and any_schema.type == "null")
        ):
            default = i
        if any_schema.ref and i == default:
            default += 1
    return default
