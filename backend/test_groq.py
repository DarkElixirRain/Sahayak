import asyncio
from core.completion.litellm_completion import LiteLLMCompletionModel
from core.models.completion import CompletionRequest

async def main():
    model = LiteLLMCompletionModel("groq_llama")
    request = CompletionRequest(
        query="Explain in one short paragraph what a legal notice is.",
        context_chunks=[],
        max_tokens=200
    )
    response = await model.complete(request)
    print("STATUS: SUCCESS")
    print("MODEL:", model.model_config["model_name"])
    print("RESPONSE:", response.completion)

if __name__ == "__main__":
    asyncio.run(main())
