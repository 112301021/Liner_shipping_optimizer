"""Base Agent class - parent for all agents"""
from abc import ABC, abstractmethod
from typing import Dict, Any
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
    def call_llm(self, user_message: str, temperature: float = 0.7) -> str:

        system_prompt = self.get_system_prompt()

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
                    user_message=user_message,
                    temperature=temperature
                )

                return response.strip()

            except Exception as e:

                logger.warning(
                    "llm_retry",
                    agent=self.name,
                    error=str(e)
                )

        logger.error("llm_failed", agent=self.name)

        return "LLM response unavailable."