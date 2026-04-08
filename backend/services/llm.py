import os
from groq import AsyncGroq
from dotenv import load_dotenv
import json

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("MODEL_NAME", "llama-3.1-8b-instant")
        self.client = AsyncGroq(api_key=self.api_key)
        print(f"DEBUG: Using Model -> {self.model}")

    async def refine_data(self, raw_text: str, url: str, hints: dict = None):
        """Refines raw scraped text into structured company intelligence using LLM."""
        
        prompt = f"""
        You are an expert lead generation analyst. Based on the following extracted text from a website ({url}), 
        extract and structure the information into a JSON format with exactly these fields:
        - company_name
        - industry
        - about (detailed summary)
        - products (comma-separated list)
        - website (canonical URL)
        - socials (JSON object with keys: linkedin, twitter, facebook, instagram, youtube. Use URLs if found, else "N/A")

        PRIORITY GUIDELINES:
        1. Always prefer a specific company's main description over generic snippets.
        2. Format products as a clean, list-like string.
        3. Identify the main industry accurately.

        Return ONLY the JSON.
        If data is not found, use "N/A".

        Website Content:
        {raw_text}
        """

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You extract structured data from website text. Respond only in JSON."},
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                response_format={"type": "json_object"}
            )
            
            # Parsing the JSON from the response
            content = response.choices[0].message.content
            data = json.loads(content)
            return data
        except Exception as e:
            return {
                "company_name": "Error",
                "industry": "Error",
                "about": f"Refinement failed: {str(e)}",
                "products": "Error",
                "website": url
            }
