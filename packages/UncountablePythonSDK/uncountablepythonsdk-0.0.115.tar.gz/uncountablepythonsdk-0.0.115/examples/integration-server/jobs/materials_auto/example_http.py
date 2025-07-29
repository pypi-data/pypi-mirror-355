from dataclasses import dataclass

from uncountable.integration.http_server import (
    GenericHttpRequest,
    GenericHttpResponse,
)
from uncountable.integration.job import CustomHttpJob, register_job
from uncountable.types import job_definition_t


@dataclass(kw_only=True)
class ExampleWebhookPayload:
    id: int
    message: str


@register_job
class HttpExample(CustomHttpJob):
    @staticmethod
    def validate_request(
        *,
        request: GenericHttpRequest,
        job_definition: job_definition_t.HttpJobDefinitionBase,
        profile_meta: job_definition_t.ProfileMetadata,
    ) -> None:
        return None

    @staticmethod
    def handle_request(
        *,
        request: GenericHttpRequest,
        job_definition: job_definition_t.HttpJobDefinitionBase,
        profile_meta: job_definition_t.ProfileMetadata,
    ) -> GenericHttpResponse:
        return GenericHttpResponse(response="OK", status_code=200)
