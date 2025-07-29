# -*- coding: utf-8 -*-
"""
Azure AI Language Service PII Detection and Redaction Tool (SDK Version)
"""
from __future__ import annotations
import logging
import os
from typing import List, Optional, Tuple

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from azure.ai.textanalytics import TextAnalyticsClient

from promptflow.core import tool
from promptflow.connections import CustomConnection

logger = logging.getLogger(__name__)

def _extract_credentials(conn: CustomConnection) -> Tuple[str, str]:
    """Extracts endpoint and API key from a CustomConnection."""
    if not isinstance(conn, CustomConnection):
        raise TypeError(f"Expected CustomConnection, got {type(conn).__name__}")

    endpoint = conn.configs.get("endpoint") or conn.configs.get("api_base")
    api_key = conn.secrets.get("api_key") or conn.secrets.get("key")

    if not endpoint:
        raise ValueError("CustomConnection must include the 'endpoint'.")
    if not api_key:
        raise ValueError("CustomConnection must include the 'api_key' in its secrets.")

    return endpoint, api_key

@tool
def redact_pii_text_sdk(
    connection: CustomConnection,
    text_input: str,
    language: str = "en",
    pii_categories: Optional[List[str]] = None,
) -> str:
    """
    Detects and redacts PII from text using the Azure Text Analytics SDK.
    """
    if not text_input or not text_input.strip():
        logger.warning("Input text is empty or whitespace only. Returning as is.")
        return text_input

    try:
        endpoint, api_key = _extract_credentials(connection)
        credential = AzureKeyCredential(api_key)
        client = TextAnalyticsClient(endpoint=endpoint, credential=credential)

        kwargs = {"language": language}
        if pii_categories and isinstance(pii_categories, list) and len(pii_categories) > 0:
            kwargs["categories_filter"] = pii_categories
            logger.info(f"Using custom PII categories filter: {pii_categories}")

        response = client.recognize_pii_entities(documents=[text_input], **kwargs)
        doc_result = response[0]

        if doc_result.is_error:
            error = doc_result.error
            logger.error(f"Azure API returned an error: Code={error.code}, Message={error.message}")
            raise RuntimeError(f"Azure API Error: {error.code} - {error.message}")
        else:
            logger.info("PII redaction successful.")
            return doc_result.redacted_text

    except ClientAuthenticationError as e:
        logger.error(f"Authentication Failed: {e}", exc_info=True)
        raise ValueError("Authentication failed. Check your API key and endpoint.") from e
    except HttpResponseError as e:
        logger.error(f"HTTP Error from Azure Service: {e}", exc_info=True)
        raise RuntimeError(f"Azure service request failed: {e.message}") from e
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise RuntimeError(f"An unexpected error occurred: {e}") from e