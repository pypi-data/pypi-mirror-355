# Cascade Inference

Cascade based inference for large language models.

## Installation

```bash
pip install cascade-inference

# To use semantic agreement, install the optional dependencies:
pip install cascade-inference[semantic]
```

## Basic Usage

> **💡 Pro-Tip:** It is highly recommended to use Level 1 client models from the same or similar model families (e.g., all Llama-based, all Qwen-based). This improves the reliability of the `semantic` agreement strategy. If you mix models from different families (like Llama and Gemini), consider lowering the `threshold` in the agreement strategy to account for stylistic differences.

Using the library is as simple as a standard OpenAI API call.

```python
from openai import OpenAI
import cascade
import os

# Setup your clients
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# Call the create function directly
response = cascade.chat.completions.create(
    # Provide the ensemble of fast clients
    level1_clients=[
        (client, "meta-llama/llama-3.1-8b-instruct"),
        (client, "google/gemini-flash-1.5")
    ],
    # Provide the single, powerful client for escalation
    level2_client=(client, "openai/gpt-4o"),
    agreement_strategy="semantic", # or "strict"
    messages=[
        {"role": "user", "content": "What are the key differences between HBM3e and GDDR7 memory?"}
    ]
)

# The response object looks just like a standard OpenAI response
print(response.choices[0].message.content)
```

## Advanced Configuration

For more control, you can pass a dictionary to the `agreement_strategy` parameter. This allows you to fine-tune the agreement logic.

### 1. Changing the Semantic Similarity Threshold

You can adjust how strictly the semantic comparison is applied. The `threshold` is a value between 0 and 1, where 1 is a perfect match. The default is `0.9`.

```python
response = cascade.chat.completions.create(
    # ... clients and messages ...
    agreement_strategy={
        "name": "semantic",
        "threshold": 0.95  # Require a 95% similarity match
    },
    # ...
)
```

### 2. Using a Different Embedding Model

The default model is `sentence-transformers/all-MiniLM-L6-v2`, which is fast and lightweight. You can specify any other model compatible with the [**`FastEmbed`** library](https://qdrant.github.io/fastembed/examples/Supported_Models/).

Some other excellent choices from the supported models list include:
*   `nomic-ai/nomic-embed-text-v1.5`
*   `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`: For multilingual use cases.

The library will automatically download and cache the new model on the first run.

```python
response = cascade.chat.completions.create(
    # ... clients and messages ...
    agreement_strategy={
        "name": "semantic",
        "model_name": "BAAI/bge-base-en-v1.5", # A larger, more powerful model
        "threshold": 0.85 # It's good practice to adjust the threshold for a new model
    },
    # ...
)
```

### 3. Using a Remote Embedding Model

If local embedding is too slow, you can use the `remote_semantic` strategy. This feature is optimized for the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index) and is the recommended way to perform remote comparisons.

**Usage:**
You must provide a Hugging Face API key, which you can get for free from your account settings: [**huggingface.co/settings/tokens**](https://huggingface.co/settings/tokens).

The key can be passed directly via the `api_key` parameter or set as the `HUGGING_FACE_HUB_TOKEN` environment variable.

The default model is `sentence-transformers/all-mpnet-base-v2`, but you can easily use other models from the [**`sentence-transformers`**](https://huggingface.co/sentence-transformers) family on the Hub. We recommend the following models for the remote strategy:

*   **Default & High-Quality:** `sentence-transformers/all-mpnet-base-v2`
*   **Lightweight & Fast:** `sentence-transformers/all-MiniLM-L6-v2`
*   **Multilingual:** `sentence-transformers/paraphrase-multilingual-mpnet-base-v2`

```python
response = cascade.chat.completions.create(
    # ... clients and messages ...
    agreement_strategy={
        "name": "remote_semantic",
        "model_name": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2", # A multilingual model
        "threshold": 0.95,
        "api_key": "hf_YourHuggingFaceToken" # Optional, can also be set via env variable
    },
    # ...
)
```

You can also point the strategy to a completely different API provider by overriding the `api_url`, but you may need to fork the `RemoteSemanticAgreement` class if the provider requires a different payload structure. 