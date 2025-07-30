import asyncio
import base64
import json
import os
from typing import AsyncGenerator, Dict, Generator, List, Optional, Union

from pip._vendor.urllib3 import HTTPResponse

from lightning_sdk.lightning_cloud.openapi.models.v1_conversation_response_chunk import V1ConversationResponseChunk
from lightning_sdk.lightning_cloud.openapi.models.v1_response_choice import V1ResponseChoice
from lightning_sdk.lightning_cloud.openapi.models.v1_response_choice_delta import V1ResponseChoiceDelta
from lightning_sdk.lightning_cloud.rest_client import LightningClient


class LLMApi:
    def __init__(self) -> None:
        self._client = LightningClient(retry=False, max_tries=0)

    def get_public_models(self) -> List[str]:
        result = self._client.assistants_service_list_assistants(published=True)
        return result.assistants

    def get_org_models(self, org_id: str) -> List[str]:
        result = self._client.assistants_service_list_assistants(org_id=org_id)
        return result.assistants

    def get_user_models(self, user_id: str) -> List[str]:
        result = self._client.assistants_service_list_assistants(user_id=user_id)
        return result.assistants

    def _stream_chat_response(self, result: HTTPResponse) -> Generator[V1ConversationResponseChunk, None, None]:
        for line in result.stream():
            decoded_lines = line.decode("utf-8").strip()
            for decoded_line in decoded_lines.splitlines():
                try:
                    payload = json.loads(decoded_line)
                    result_data = payload.get("result", {})

                    choices = []
                    for choice in result_data.get("choices", []):
                        delta = choice.get("delta", {})
                        choices.append(
                            V1ResponseChoice(
                                delta=V1ResponseChoiceDelta(**delta),
                                finish_reason=choice.get("finishReason"),
                                index=choice.get("index"),
                            )
                        )

                    yield V1ConversationResponseChunk(
                        choices=choices,
                        conversation_id=result_data.get("conversationId"),
                        executable=result_data.get("executable"),
                        id=result_data.get("id"),
                        throughput=result_data.get("throughput"),
                    )

                except json.JSONDecodeError:
                    print("Error decoding JSON:", decoded_line)

    def _encode_image_bytes_to_data_url(self, image: str) -> str:
        with open(image, "rb") as image_file:
            b64 = base64.b64encode(image_file.read()).decode("utf-8")
            extension = image.split(".")[-1]
            return f"data:image/{extension};base64,{b64}"

    def start_conversation(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_completion_tokens: int,
        assistant_id: str,
        images: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        billing_project_id: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Union[V1ConversationResponseChunk, Generator[V1ConversationResponseChunk, None, None]]:
        is_internal_conversation = os.getenv("LIGHTNING_INTERNAL_CONVERSATION", "false").lower() == "true"
        body = {
            "message": {
                "author": {"role": "user"},
                "content": [
                    {"contentType": "text", "parts": [prompt]},
                ],
            },
            "max_completion_tokens": max_completion_tokens,
            "conversation_id": conversation_id,
            "billing_project_id": billing_project_id,
            "name": name,
            "stream": stream,
            "metadata": metadata or {},
            "internal_conversation": is_internal_conversation,
        }
        if images:
            for image in images:
                url = image
                if not image.startswith("http"):
                    url = self._encode_image_bytes_to_data_url(image)

                body["message"]["content"].append(
                    {
                        "contentType": "image",
                        "parts": [url],
                    }
                )

        result = self._client.assistants_service_start_conversation(body, assistant_id, _preload_content=not stream)
        if not stream:
            return result.result
        return self._stream_chat_response(result)

    async def async_start_conversation(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_completion_tokens: int,
        assistant_id: str,
        images: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        billing_project_id: Optional[str] = None,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        stream: bool = False,
    ) -> Union[V1ConversationResponseChunk, AsyncGenerator[V1ConversationResponseChunk, None]]:
        is_internal_conversation = os.getenv("LIGHTNING_INTERNAL_CONVERSATION", "false").lower() == "true"
        body = {
            "message": {
                "author": {"role": "user"},
                "content": [
                    {"contentType": "text", "parts": [prompt]},
                ],
            },
            "max_completion_tokens": max_completion_tokens,
            "conversation_id": conversation_id,
            "billing_project_id": billing_project_id,
            "name": name,
            "stream": stream,
            "metadata": metadata or {},
            "internal_conversation": is_internal_conversation,
        }
        if images:
            for image in images:
                url = image
                if not image.startswith("http"):
                    url = self._encode_image_bytes_to_data_url(image)

                body["message"]["content"].append(
                    {
                        "contentType": "image",
                        "parts": [url],
                    }
                )

        if not stream:
            thread = await asyncio.to_thread(
                self._client.assistants_service_start_conversation, body, assistant_id, async_req=True
            )
            result = await asyncio.to_thread(thread.get)
            return result.result

        raise NotImplementedError("Streaming is not supported in this client.")

    def list_conversations(self, assistant_id: str) -> List[str]:
        result = self._client.assistants_service_list_conversations(assistant_id)
        return result.conversations

    def get_conversation(self, assistant_id: str, conversation_id: str) -> V1ConversationResponseChunk:
        result = self._client.assistants_service_get_conversation(assistant_id, conversation_id)
        return result.messages

    def reset_conversation(self, assistant_id: str, conversation_id: str) -> None:
        self._client.assistants_service_delete_conversation(assistant_id, conversation_id)
