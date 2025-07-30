import asyncio
import functools
from cascade.strategies import StrictAgreement, SemanticAgreement, RemoteSemanticAgreement

STRATEGY_MAPPING = {
    "strict": StrictAgreement,
    "semantic": SemanticAgreement,
    "remote_semantic": RemoteSemanticAgreement,
}

def create(level1_clients, level2_client, agreement_strategy, messages, **kwargs):
    """
    Synchronous wrapper for the core async cascade logic.
    Provides a simple, blocking API similar to openai.create().
    """
    return asyncio.run(_async_create(
        level1_clients, 
        level2_client, 
        agreement_strategy, 
        messages, 
        **kwargs
    ))

async def _async_create(level1_clients, level2_client, agreement_strategy, messages, **kwargs):
    """
    This is the main async function for Cascade Inference.
    It performs level 1 inference calls asynchronously and prepares for comparison.
    """
    
    tasks = []
    for client, model in level1_clients:
        call = functools.partial(
            client.chat.completions.create, 
            model=model, 
            messages=messages, 
            **kwargs
        )
        tasks.append(asyncio.to_thread(call))

    level1_responses = await asyncio.gather(*tasks)

    #for response in level1_responses:
    #    print(response.choices[0].message.content)

    strategy_name = None
    strategy_params = {}

    if isinstance(agreement_strategy, str):
        strategy_name = agreement_strategy
    elif isinstance(agreement_strategy, dict):
        strategy_name = agreement_strategy.get("name")
        strategy_params = {k: v for k, v in agreement_strategy.items() if k != "name"}
    else:
        raise TypeError("agreement_strategy must be a string or a dictionary.")

    strategy_class = STRATEGY_MAPPING.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"Unknown agreement strategy: {strategy_name}")
    
    strategy = strategy_class(**strategy_params)
    agreed = strategy.check_agreement(level1_responses)

    if agreed:
        #print("Level 1 clients agreed. Returning first response.")
        return level1_responses[0]
    else:
        #print("Level 1 clients disagreed. Escalating to Level 2 client.")
        
        l2_client, l2_model = level2_client

        call = functools.partial(
            l2_client.chat.completions.create,
            model=l2_model,
            messages=messages,
            **kwargs
        )
        
        level2_response = await asyncio.to_thread(call)
        
        #print("Received response from Level 2 client.")
        return level2_response 