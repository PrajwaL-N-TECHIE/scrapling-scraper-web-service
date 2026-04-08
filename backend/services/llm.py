import os
from groq import AsyncGroq
from dotenv import load_dotenv
import json

load_dotenv()

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        # Load priority list of models
        fallback_str = os.getenv("FALLBACK_MODELS", "openai/gpt-oss-120b,llama-3.3-70b-versatile")
        self.priority_models = [m.strip() for m in fallback_str.split(",") if m.strip()]
        
        self.client = AsyncGroq(api_key=self.api_key)
        print(f"DEBUG: LLM Initialized with {len(self.priority_models)} potential models.")

    async def refine_data(self, raw_text: str, url: str, hints: dict = None):
        """Refines raw scraped text using a prioritized list of models with automatic fallback."""
        
        # Truncate text to avoid Rate Limit (TPM) issues on Groq
        truncated_text = raw_text[:15000]
        
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
        {truncated_text}
        """

        last_error = None
        for model in self.priority_models:
            try:
                print(f"DEBUG: Attempting refinement with model -> {model}")
                response = await self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You extract structured data from website text. Respond only in JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    model=model,
                    response_format={"type": "json_object"}
                )
                
                # Parsing the JSON from the response
                content = response.choices[0].message.content
                data = json.loads(content)
                return data

            except Exception as e:
                print(f"WARNING: Model {model} failed: {str(e)}")
                last_error = str(e)
                continue # Try next model

        # If we reach here, all models failed
        return {
            "company_name": "Error",
            "industry": "Error",
            "about": f"All fallback models failed. Last error: {last_error}",
            "products": "Error",
            "website": url
        }
