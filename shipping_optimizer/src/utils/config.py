import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    LOGS_DIR = PROJECT_ROOT/ "logs"
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL","llama-3.3-70b-versatile" )
    REGIONAL_MODEL = os.getenv("REGIONAL_MODEL", "llama-3.3-70b-versatile")
    
    GA_POPULATION_SIZE = int(os.getenv("GA_POPULATION_SIZE", "20"))
    GA_GENERATIONS = int(os.getenv("GA_GENERATIONS", "50"))
    MILP_TIME_LIMIT = int(os.getenv("MILP_TIME_LIMIT", "60"))
    
    @classmethod
    def validate(cls):

        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not found!\n"
                "Please set it in your .env file"
            )

        if not cls.GROQ_API_KEY.startswith("gsk_"):
            raise ValueError(
                "Invalid GROQ API key format"
            )

        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.LOGS_DIR.mkdir(exist_ok=True)

        print("✓ Configuration validated")
Config.validate()
        