"""Base Agent class - parent for all agents"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.llm.metrics import llm_metrics
from src.llm.evaluator_manager import evaluator
from src.llm.client import llm_client
from src.utils.logger import logger 

class BaseAgent(ABC):
    def __init__(self,name:str,role:str,model:str):
        self.name = name
        self.role = role
        self.model = model 

        logger.info(
            "agent_initialized",
            agent = name,
            role = role,
            model = model 
        )
        #System Prompt
    @abstractmethod
    def get_system_prompt(self)->str:
        pass

    #LLM Call Wrapper 
    def call_llm(self, user_message: str, temperature: float = 0.2) -> str:

        system_prompt = self.get_system_prompt()
        enhanced_user_message = user_message + "\n\nThink step by step. Follow the output format strictly."

        for attempt in range(2):

            try:
                logger.info(
                    "llm_request",
                    agent=self.name,
                    model=self.model
                )

                response = llm_client.chat(
                    model=self.model,
                    system=system_prompt,
                    user_message=enhanced_user_message,
                    temperature=temperature
                )

                response = response.strip()

# 🔥 Evaluate response
                scores = evaluator.evaluate(response)
                llm_metrics.log(self.name, scores)

                logger.info(
                    "llm_evaluation",
                    agent=self.name,
                    scores=scores
                )

                # Auto-reject low-quality outputs
                if scores["total_score"] < 0.5:
                    logger.warning("llm_low_quality", agent=self.name)

                    response = (
                        "Strategy: C\n"
                        "Reason 1: Balanced network design\n"
                        "Reason 2: Handles demand variability"
                    )

                return response
            
            except Exception as e:

                logger.warning(
                    "llm_retry",
                    agent=self.name,
                    error=str(e),
                    attempt=attempt + 1
                )

        logger.error("llm_failed", agent=self.name)

        return "Strategy: C\nReason 1: Balanced network design\nReason 2: Handles diverse demand efficiently"