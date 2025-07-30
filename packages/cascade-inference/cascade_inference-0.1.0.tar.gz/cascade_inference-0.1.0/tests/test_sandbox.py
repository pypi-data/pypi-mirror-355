import pytest
import os
import openai
import cascade
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

@pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not set")
def test_live_create_completion():
    """
    Tests the create completion function with a live OpenRouter endpoint.
    This is a basic sandbox test to ensure the async calls and aggregation work.
    """
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

    level1_clients = [
        (client, "meta-llama/llama-3.1-8b-instruct"),
        (client, "meta-llama/llama-3.2-3b-instruct")
    ]
    
    level2_client = (client, "openai/gpt-4o")

    messages = [
        {"role": "user", "content": "Write a hello world program in python"}
    ]

    response = cascade.chat.completions.create(
        level1_clients=level1_clients,
        level2_client=level2_client,
        agreement_strategy={
            "name": "semantic",
        },
        messages=messages,
    )

    assert response is not None, "Response object should not be None"
    assert hasattr(response, 'choices'), "Response object should have 'choices' attribute"
    assert len(response.choices) > 0, "Response should have at least one choice"
    
    message = response.choices[0].message
    assert hasattr(message, 'content'), "Message object should have 'content' attribute"
    assert isinstance(message.content, str), "Message content should be a string"
    assert len(message.content) > 0, "Message content should not be empty"

    print(f"\nReceived response from model: {message.content}") 