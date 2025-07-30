import pytest
from cascade.chat import completions

# --- Mock Objects for Testing ---

class MockMessage:
    def __init__(self, content):
        self.content = content

class MockChoice:
    def __init__(self, content="This is a mock response."):
        self.message = MockMessage(content)

class MockResponse:
    """The object that the 'create' method should return. It contains the list of choices."""
    def __init__(self):
        self.choices = [MockChoice()]

class MockCompletion:
    def __init__(self):
        # The create method now returns the full MockResponse object
        self.create = lambda **kwargs: MockResponse()

class MockChat:
    def __init__(self):
        self.completions = MockCompletion()

class MockClient:
    def __init__(self, name="mock"):
        self.name = name
        self.chat = MockChat()

# --- Test Functions ---

# Helper to check if semantic dependencies are installed
def is_semantic_installed():
    try:
        import fastembed
        return True
    except ImportError:
        return False

@pytest.mark.skipif(not is_semantic_installed(), reason="Requires 'fastembed' dependencies")
def test_create_completion_semantic():
    """
    Tests the basic functionality with the 'semantic' agreement strategy.
    """
    level1_clients = [
        (MockClient("phi3"), "model1"),
        (MockClient("gemma"), "model2")
    ]
    level2_client = (MockClient("claude"), "model3")

    messages = [{"role": "user", "content": "Test prompt"}]

    response = completions.create(
        level1_clients=level1_clients,
        level2_client=level2_client,
        agreement_strategy="semantic",
        messages=messages,
    )

    assert response is not None
    assert hasattr(response, 'choices')
    assert len(response.choices) == 1
    assert hasattr(response.choices[0], 'message')
    assert response.choices[0].message.content == "This is a mock response."

def test_create_completion_strict():
    """
    Tests the basic functionality with the 'strict' agreement strategy.
    This test has no external dependencies.
    """
    level1_clients = [
        (MockClient("phi3"), "model1"),
        (MockClient("gemma"), "model2")
    ]
    level2_client = (MockClient("claude"), "model3")

    messages = [{"role": "user", "content": "Test prompt"}]

    response = completions.create(
        level1_clients=level1_clients,
        level2_client=level2_client,
        agreement_strategy="strict",
        messages=messages,
    )

    assert response is not None
    assert hasattr(response, 'choices')
    assert response.choices[0].message.content == "This is a mock response." 