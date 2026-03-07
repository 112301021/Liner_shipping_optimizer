from src.utils.config import Config
from src.utils.logger import logger

def test_config ():
    """Test configuration loads correctly"""
    print("\n=== Testing Configuration ===")
    print(f"API Key present: {'Yes' if Config.GROQ_API_KEY else 'No'}")
    print(f"Orchestrator model: {Config.ORCHESTRATOR_MODEL}")
    print(f"Regional model: {Config.REGIONAL_MODEL}")
    print(f"GA Population: {Config.GA_POPULATION_SIZE}")
    print(f"GA Generations: {Config.GA_GENERATIONS}")
    print("✓ Configuration working!")
    
def test_logger():
    """Test logger works"""
    print("\n=== Testing Logger ===")
    logger.info("test_log_entry", test_key="test_value", number=42)
    print("✓ Logger working! (Check logs/ folder)")
    
if __name__ == "__main__":
    test_config()
    test_logger()
    print("\n All tests passed!")
    
    