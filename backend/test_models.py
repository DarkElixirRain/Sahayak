import asyncio
from core.completion.litellm_completion import LiteLLMCompletionModel
from core.models.completion import CompletionRequest
import traceback

async def test_model(model_name):
    print(f"Testing {model_name}...")
    model = LiteLLMCompletionModel("groq_llama")
    model.model_config["model_name"] = model_name  # override
    request = CompletionRequest(
        query="Say hi", context_chunks=[], max_tokens=10
    )
    try:
        response = await model.complete(request)
        print(f"SUCCESS: {model_name}")
        print("Response:", response.completion)
        return True
    except Exception as e:
        print(f"FAILED: {model_name} - {str(e)[:100]}")
        return False

async def main():
    models = ["groq/qwen/qwen3.8-27b", "groq/groq/compound", "groq/openai/gpt-oss-20b"]
    for m in models:
        if await test_model(m):
            break

if __name__ == "__main__":
    asyncio.run(main())
