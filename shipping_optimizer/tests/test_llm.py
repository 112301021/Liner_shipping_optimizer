from src.llm.client import llm_client
from src.utils.config import Config

def test_simple_call():
    print("\n=== Testing LLM Client ===")
    print("Calling GROQ API...")
    response = llm_client.chat(
        model=Config.REGIONAL_MODEL,
        system="You are a helpful assistant.",
        user_message="Say 'Hello from GROQ!' and nothing else."
    )
    print(f"Response: {response}")
    assert "Hello" in response or "hello" in response
    print("✓ LLM client working!")

def test_cache():
    print("\n=== Testing Cache ===")
    # First call
    response1 = llm_client.chat(
        model=Config.REGIONAL_MODEL,
        system="You are a helpful assistant.",
        user_message="Count to 3"
    )
    # Second call (should be cached)
    response2 = llm_client.chat(
        model=Config.REGIONAL_MODEL,
        system="You are a helpful assistant.",
        user_message="Count to 3"
    )
    assert response1 == response2
    print("✓ Cache working!")

if __name__ == "__main__":
    test_simple_call()
    test_cache()
    print("\n All LLM tests passed!")
    
    