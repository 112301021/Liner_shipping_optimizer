from groq import Groq
from src.utils.logger import logger
from src.utils.config import Config

class LLMClient:
    
    def __init__(self):
        self.client = Groq(api_key = Config.GROQ_API_KEY)
        self.cache = {}
        
        self.total_calls = 0
        self.cache_hits = 0
        
    def chat(
        self,
        model: str,
        system : str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens:int = 2000
        ) -> str:
        
        self.total_calls += 1
        cache_key = f"{model}:{hash(system)}:{hash(user_message)}"
        
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.info("llm_cache_hit",hit_rate=f"{self.cache_hits}/{self.total_calls}")
            return self.cache[cache_key]
        
        try:
            logger.info("llm_calling", model = model)
            response = self.client.chat.completions.create(
                model = model,
                messages=[
                    {"role":"system","content": system},
                    {"role": "user","content":user_message}
                ],
                temperature= temperature,
                max_tokens= max_tokens   
            )
            result = response.choices[0].message.content
            logger.info(
                "llm_success",
                model=model,
                prompt_tokens = response.usage.prompt_tokens,
                completion_tokens = response.usage.completion_tokens
            )
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            logger.error("llm_error", error=str(e))
            raise

llm_client = LLMClient()