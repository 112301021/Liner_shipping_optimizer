import os
from pathlib import Path
from dotenv import load_dotenv


class Config:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    load_dotenv(PROJECT_ROOT / ".env")
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT/ "logs"
    
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL","openrouter/gpt-oss-120b" )
    REGIONAL_MODEL = os.getenv("REGIONAL_MODEL", "meta-llama/llama-3.1-8b-instruct")
    
    GA_POPULATION_SIZE = int(os.getenv("GA_POPULATION_SIZE", "80"))
    GA_GENERATIONS = int(os.getenv("GA_GENERATIONS", "120"))
    MILP_TIME_LIMIT = int(os.getenv("MILP_TIME_LIMIT", "120"))
    
    @classmethod
    def validate(cls):

        if not cls.OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY not found!\n"
                "Please set it in your .env file"
            )

        if not cls.OPENROUTER_API_KEY.startswith("sk-or-"):
            raise ValueError(
                "Invalid OPENROUTER_API_KEY format"
            )

        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)

        print("✓ Configuration validated")
Config.validate()
        