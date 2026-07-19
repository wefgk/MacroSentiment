import json
import logging
from openai import AsyncOpenAI
import time

logger=logging.getLogger(__name__)

class AIAnalyzer:
    def __init__(self,url:str,api_key:str):
        self.client=AsyncOpenAI(base_url=url,api_key=api_key)

    async def analyze_sentiment(self, text: str, geo_entities: list[str], model: str = "") -> dict[str, float]:
        entities_str = ", ".join(geo_entities)
        
        system_prompt = (
            "You are a cautious and deeply analytical geopolitical expert. Your goal is to provide realistic, "
            "highly calibrated sentiment scores without exaggeration. Avoid extreme scores for routine actions.\n\n"
            
            f"Task: Output scores strictly for these exact entities: {entities_str}.\n\n"
            
            "Score Calibration Guide:\n"
            "+1.0 to +0.8: World-changing peace, historic alliances, massive trade treaties.\n"
            "+0.5 to +0.3: Major bilateral deals, massive long-term investments, successful high-level diplomacy.\n"
            "+0.2 to +0.1: Minor tactical success, regular state cooperation, routine positive development.\n"
            "0.0: Neutral events, natural disasters, no geopolitical shift.\n"
            "-0.1 to -0.2: Verbal threats, local tariffs, routine political friction.\n"
            "-0.3 to -0.5: Severe sanctions, localized military strikes, border clashes, economic damage.\n"
            "-0.8 to -1.0: Full-scale war outbreak, total diplomatic collapse, massive devastation.\n\n"
            
            "CRITICAL RULES:\n"
            "1. Be conservative. A military strike is a tactical action (-0.4 for target), NOT a grand victory for the attacker. Attacker score should be close to 0.0 (+0.1 or +0.2 max if successful).\n"
            "2. If an entity is not active or mentioned, score it strictly 0.0.\n"
            "3. Do NOT write any introduction, reasoning, or explanations. Generate only the numbers inside the JSON structure."
        )

        ratings_properties = {entity: {"type": "number"} for entity in geo_entities}
        
        schema = {
            "type": "json_schema",
            "json_schema": {
                "name": "sentiment_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "ratings": {
                            "type": "object",
                            "properties": ratings_properties,
                            "required": geo_entities,
                            "additionalProperties": False
                        }
                    },
                    "required": ["ratings"],
                    "additionalProperties": False
                }
            }
        }

        start_time=time.perf_counter()
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=[{
                    "role": "user", 
                    "content": f"{system_prompt}\n\nAnalyze this text:\n{text}"
                }],
                temperature=0.0,
                max_tokens=60,  
                response_format=schema
            )
            
            raw_content = response.choices[0].message.content.strip()
            
            
            if raw_content.startswith("```"):
                raw_content = raw_content.strip("`").replace("json", "", 1).strip()
                
            parsed_json = json.loads(raw_content)
            
            ai_ratings = parsed_json.get("ratings", {})
            #logger.info(f"ai_ratings - {ai_ratings}")

            if not isinstance(ai_ratings, dict):
                logger.error(f"AI has destroyed the structure")
                return {}

            clean_result = {
                key: float(value) 
                for key, value in ai_ratings.items() 
                if key in geo_entities
            }
            
            execution_time=time.perf_counter()-start_time
            logger.info(f"AI time spent on analyzing - {execution_time:.2f}")
            return clean_result
            
        except json.JSONDecodeError:
            logger.error(f"The AI ​​failed to return pure JSON. The response was: {raw_content}")
            return {}
        except Exception as e:
            logger.error(f"API error: {e}")
            return {}