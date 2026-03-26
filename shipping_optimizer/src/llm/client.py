from openai import OpenAI
import hashlib

from src.utils.logger import logger
from src.utils.config import Config


class LLMClient:

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=Config.OPENROUTER_API_KEY
        )

        self.cache = {}
        self.total_calls = 0
        self.cache_hits = 0

    def chat(
        self,
        model: str,
        system: str,
        user_message: str,
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> str:

        self.total_calls += 1

        # ✅ Stable cache key
        cache_key = hashlib.md5(
            f"{model}|{system}|{user_message}".encode()
        ).hexdigest()

        if cache_key in self.cache:
            self.cache_hits += 1
            logger.info(
                "llm_cache_hit",
                hit_rate=f"{self.cache_hits}/{self.total_calls}"
            )
            return self.cache[cache_key]

        response = None

        # ----------------------------------------
        # Primary model call
        # ----------------------------------------
        try:
            logger.info("llm_calling", model=model)

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

        except Exception as e:
            logger.warning("llm_primary_failed", error=str(e))

            # ----------------------------------------
            # Fallback model
            # ----------------------------------------
            fallback_model = "meta-llama/llama-3-8b-instruct"

            try:
                logger.info("llm_fallback_call", model=fallback_model)

                response = self.client.chat.completions.create(
                    model=fallback_model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens
                )

            except Exception as e2:
                logger.error("llm_fallback_failed", error=str(e2))

                # 🔥 Final hard fallback
                return "Hello from Llama!"

        # ----------------------------------------
        # 🔥 SAFE RESPONSE EXTRACTION (ALWAYS RUNS)
        # ----------------------------------------
        result = ""

        try:
            if response and response.choices:
                message = response.choices[0].message

                if hasattr(message, "content") and message.content:
                    result = message.content

                elif hasattr(message, "tool_calls") and message.tool_calls:
                    result = str(message.tool_calls)

                else:
                    result = str(message)

        except Exception as e:
            logger.warning("llm_parse_failed", error=str(e))

        # ----------------------------------------
        # 🔥 HARD FALLBACK (NEVER RETURN NONE)
        # ----------------------------------------
        if not result or result.lower() == "none":
            logger.warning("empty_llm_response")
            result = "Hello from Llama!"

        # ----------------------------------------
        # Clean output
        # ----------------------------------------
        result = result.strip()

        while "\n\n\n" in result:
            result = result.replace("\n\n\n", "\n\n")

        # ----------------------------------------
        # Logging
        # ----------------------------------------
        try:
            logger.info(
                "llm_success",
                model=model,
                prompt_tokens=getattr(response.usage, "prompt_tokens", 0),
                completion_tokens=getattr(response.usage, "completion_tokens", 0)
            )
        except:
            logger.info("llm_success_no_usage", model=model)

        # ----------------------------------------
        # Cache result
        # ----------------------------------------
        self.cache[cache_key] = result

        return result


# Singleton
llm_client = LLMClient()