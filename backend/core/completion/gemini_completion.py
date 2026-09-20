import logging
import os
from typing import AsyncGenerator, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel

from core.models.completion import CompletionRequest, CompletionResponse

from .base_completion import BaseCompletionModel

logger = logging.getLogger(__name__)


def get_system_message(inline_citations: bool = False) -> str:
    """Return the standard system message for Morphik's query agent."""
    if inline_citations:
        return """You are Morphik's powerful query agent with INLINE CITATION MODE ENABLED.

MANDATORY CITATION RULES:
- Every fact or piece of information from the context MUST include its source citation
- Citations appear as "Source: [filename, page X]" or "Source: [filename]" at the end of each context chunk
- Copy these citations EXACTLY in your response using the format [filename, page X]
- Place citations immediately after the relevant information

Your role is to:
1. Analyze the provided context chunks from documents carefully
2. Use the context to answer questions accurately with proper citations
3. Be clear and concise in your answers
4. ALWAYS include [filename, page X] citations for every piece of information
5. For image-based queries, analyze the visual content with citations
6. Format your responses using Markdown

Example response with citations:
"Morphik is a retrieval-augmented generation tool [README.md, page 1] designed for legal and technical work [overview.pdf, page 3]."

Remember: NO information should be presented without its source citation."""
    else:
        return """You are Morphik's powerful query agent. Your role is to:

1. Analyze the provided context chunks from documents carefully
2. Use the context to answer questions accurately and comprehensively
3. Be clear and concise in your answers
4. When relevant, cite specific parts of the context to support your answers
5. For image-based queries, analyze the visual content in conjunction with any text context provided
6. Format your responses using Markdown.

Remember: Your primary goal is to provide accurate, context-aware responses that help users understand
and utilize the information in their documents effectively."""


def format_user_content(
    context_text: List[str],
    query: str,
    prompt_template: Optional[str] = None,
    inline_citations: bool = False,
    chunk_metadata: Optional[List[Dict]] = None,
) -> str:
    """Format the user content based on context and query."""
    if inline_citations and chunk_metadata:
        formatted_chunks = []
        for chunk, metadata in zip(context_text, chunk_metadata):
            filename = metadata.get("filename", "unknown")
            page = metadata.get("page_number")
            is_colpali = metadata.get("is_colpali", False)

            if is_colpali and page:
                citation = f"[{filename}, page {page}]"
            elif page:
                citation = f"[{filename}, page {page}]"
            else:
                citation = f"[{filename}]"

            formatted_chunks.append(f"{chunk}\nSource: {citation}")
        context = "\n" + "\n\n".join(formatted_chunks) + "\n\n"
    else:
        context = "\n" + "\n\n".join(context_text) + "\n\n" if context_text else ""

    if prompt_template:
        return prompt_template.format(context=context, question=query, query=query)
    elif context_text:
        return f"Context: {context} Question: {query}"
    else:
        return query


class GeminiCompletionModel(BaseCompletionModel):
    """
    Direct Gemini API completion model implementation.
    Uses the google-genai library to directly call Gemini API.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini completion model.

        Args:
            model_name: The Gemini model name (e.g., "gemini-1.5-flash", "gemini-1.5-pro")
        """
        self.model_name = model_name
        
        # Get API key from environment
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable must be set")
        
        # Gemini API endpoint
        self.api_base = "https://generativelanguage.googleapis.com/v1beta/models"
        
        logger.info(f"Initialized Gemini completion model with model={model_name}")

    async def complete(
        self, request: CompletionRequest
    ) -> Union[CompletionResponse, AsyncGenerator[str, None]]:
        """
        Generate completion using Gemini API.

        Args:
            request: CompletionRequest object containing query, context, and parameters

        Returns:
            CompletionResponse object with the generated text and usage statistics
        """
        # Extract text context (ignore images for now)
        context_text = [
            chunk for chunk in request.context_chunks if not chunk.startswith("data:image/")
        ]

        # Format user content
        user_content = format_user_content(
            context_text,
            request.query,
            request.prompt_template,
            request.inline_citations,
            request.chunk_metadata,
        )

        # Build system instruction
        system_instruction = (
            request.system_prompt
            if request.system_prompt
            else get_system_message(request.inline_citations)
        )

        # Prepare request payload for Gemini API
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_content}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "temperature": request.temperature if request.temperature is not None else 0.3,
                "maxOutputTokens": request.max_tokens if request.max_tokens is not None else 8192,
            }
        }

        try:
            # Call Gemini API using httpx
            url = f"{self.api_base}/{self.model_name}:generateContent?key={self.api_key}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0,
                )
                
                if response.status_code != 200:
                    error_msg = f"Gemini API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                result = response.json()
                
                # Extract the response text
                completion_text = result["candidates"][0]["content"]["parts"][0]["text"]
                
                # Extract usage information if available
                usage_metadata = result.get("usageMetadata", {})
                usage = {
                    "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                    "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                    "total_tokens": usage_metadata.get("totalTokenCount", 0),
                }
                
                return CompletionResponse(
                    completion=completion_text,
                    usage=usage,
                    finish_reason="stop",
                )

        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise
