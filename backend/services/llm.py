import os
import httpx
import certifi
import traceback
from groq import AsyncGroq, APIConnectionError, APIStatusError
from dotenv import load_dotenv
import json

load_dotenv()

class LLMService:
    def __init__(self):
        raw_key = os.getenv("GROQ_API_KEY")
        self.api_key = raw_key.strip() if raw_key else None
        
        if not self.api_key:
            print("CRITICAL: GROQ_API_KEY is not set (or is empty) in environment variables!")
        
        # Load priority list of models (Optimized for stability)
        default_models = "llama-3.3-70b-versatile,mixtral-8x7b-32768,llama-3.1-8b-instant"
        fallback_str = os.getenv("FALLBACK_MODELS", default_models)
        self.priority_models = [m.strip() for m in fallback_str.split(",") if m.strip()]
        
        # 'Deep Fix' Config: Use certifi bundle and FORCE HTTP/1.1 (many proxies hate HTTP/2)
        http_client = httpx.AsyncClient(
            verify=certifi.where(),
            http2=False, # Disable HTTP/2 for maximum compatibility
            timeout=30.0
        )
        self.client = AsyncGroq(api_key=self.api_key, http_client=http_client)
        print(f"DEBUG: LLM Initialized. Key present: {bool(self.api_key)}. Models: {len(self.priority_models)}")

    async def refine_data(self, raw_text: str, url: str, hints: dict = None):
        """Refines raw scraped text using a prioritized list of models with automatic fallback."""
        
        if not self.api_key:
            return {
                "company_name": "Configuration Error",
                "industry": "N/A",
                "about": "GROQ_API_KEY is missing/empty. Please add it to your environment variables on Render (and make sure to SAVE the settings).",
                "products": "N/A",
                "website": url
            }

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

            except APIConnectionError as e:
                err_msg = f"Connection Error for {model}: {str(e)}"
                print(f"WARNING: {err_msg}")
                traceback.print_exc() # Print full traceback to Render logs
                last_error = err_msg
                continue
            except APIStatusError as e:
                err_msg = f"Status Error {e.status_code} for {model}: {e.message}"
                print(f"WARNING: {err_msg}")
                last_error = err_msg
                if e.status_code == 401:
                    break # Don't try other models if the API Key is invalid
                continue
            except Exception as e:
                err_msg = f"Unexpected Error for {model}: {str(e)}"
                print(f"WARNING: {err_msg}")
                traceback.print_exc()
                last_error = err_msg
                continue

        # If we reach here, all models failed
        return {
            "company_name": "Error",
            "industry": "Error",
            "about": f"Refinement failed. Details: {last_error}",
            "products": "Error",
            "website": url
        }
