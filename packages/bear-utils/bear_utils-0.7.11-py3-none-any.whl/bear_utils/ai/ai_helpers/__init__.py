from collections.abc import Callable
from typing import Any

from ...logging import BaseLogger
from ._common import GPT_4_1, GPT_4_1_MINI, GPT_4_1_NANO, PRODUCTION_MODE, TESTING_MODE, AIModel, EnvironmentMode
from ._config import AIEndpointConfig
from ._parsers import JSONResponseParser, ModularAIEndpoint, PassthroughResponseParser, TypedResponseParser


def create_typed_endpoint[T_Response](
    response_type: type[T_Response],
    project_name: str,
    prompt: str,
    testing_url: str,
    production_url: str,
    logger: BaseLogger,
    transformers: dict[str, Callable] | None = None,
    environment: EnvironmentMode = PRODUCTION_MODE,
    chat_model: AIModel = GPT_4_1_NANO,
    **kwargs,
) -> ModularAIEndpoint[T_Response]:
    """Create an endpoint with strict TypedDict response typing."""
    config = AIEndpointConfig(
        project_name=project_name,
        prompt=prompt,
        testing_url=testing_url,
        production_url=production_url,
        environment=environment,
        chat_model=chat_model,
        **kwargs,
    )
    parser = TypedResponseParser(default_response=response_type, response_transformers=transformers)
    return ModularAIEndpoint(config, logger, parser)  # type: ignore[return-value, arg-type]


def create_command_endpoint[T_Response](
    default_response: T_Response,
    project_name: str,
    prompt: str,
    testing_url: str,
    production_url: str,
    logger: BaseLogger,
    environment: EnvironmentMode = EnvironmentMode.PRODUCTION,
    chat_model: AIModel = GPT_4_1_NANO,
    **kwargs,
) -> ModularAIEndpoint[T_Response]:
    from rich.markdown import Markdown

    config = AIEndpointConfig(
        project_name=project_name,
        prompt=prompt,
        testing_url=testing_url,
        production_url=production_url,
        environment=environment,
        chat_model=chat_model,
        **kwargs,
    )

    parser = TypedResponseParser(
        default_response=default_response,
        response_transformers={"response": lambda x: Markdown(str(x))},
    )

    return ModularAIEndpoint(config, logger, parser)


def create_flexible_endpoint(
    project_name: str,
    prompt: str,
    testing_url: str,
    production_url: str,
    logger: BaseLogger,
    required_fields: list | None = None,
    transformers: dict[str, Callable] | None = None,
    append_json: bool = True,
    environment: EnvironmentMode = PRODUCTION_MODE,
    chat_model: AIModel = GPT_4_1_NANO,
    **kwargs,
) -> ModularAIEndpoint[dict[str, Any]]:
    """Create an endpoint with flexible JSON parsing."""
    config = AIEndpointConfig(
        project_name=project_name,
        prompt=prompt,
        testing_url=testing_url,
        production_url=production_url,
        append_json_suffix=append_json,
        environment=environment,
        chat_model=chat_model,
        **kwargs,
    )
    parser = JSONResponseParser(required_fields, transformers)
    return ModularAIEndpoint(config, logger, parser)


def create_simple_endpoint(
    project_name: str,
    prompt: str,
    testing_url: str,
    production_url: str,
    logger: BaseLogger,
    environment: EnvironmentMode = PRODUCTION_MODE,
    chat_model: AIModel = GPT_4_1_NANO,
    **kwargs,
) -> ModularAIEndpoint[dict[str, Any]]:
    """Create an endpoint that returns raw output without JSON parsing."""
    config = AIEndpointConfig(
        project_name=project_name,
        prompt=prompt,
        testing_url=testing_url,
        production_url=production_url,
        append_json_suffix=False,
        environment=environment,
        chat_model=chat_model,
        **kwargs,
    )
    parser = PassthroughResponseParser()
    return ModularAIEndpoint(config, logger, parser)


__all__: list[str] = [
    "create_typed_endpoint",
    "create_command_endpoint",
    "create_flexible_endpoint",
    "create_simple_endpoint",
    "AIEndpointConfig",
    "EnvironmentMode",
    "PRODUCTION_MODE",
    "TESTING_MODE",
    "ModularAIEndpoint",
]
