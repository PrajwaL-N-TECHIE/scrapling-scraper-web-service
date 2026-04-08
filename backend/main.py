from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import io
import asyncio
from services.scraper import ScraperService
from services.llm import LLMService
import uuid

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = ScraperService()
llm = LLMService()

class ScrapeRequest(BaseModel):
    url: str

class BulkScrapeRequest(BaseModel):
    urls: List[str]

class ScrapeResponse(BaseModel):
    company_name: str
    industry: str
    about: str
    products: str
    website: str
    socials: Dict[str, str]

@app.get("/")
def read_root():
    return {"message": "AI Scraper API is running!"}

@app.post("/scrape")
async def scrape_single(request: ScrapeRequest):
    print(f"Requesting scrape for: {request.url}")
    result = await scraper.scrape_url(request.url)
    
    if result["status"] == "error":
        error_msg = result.get("error", "Unknown error")
        print(f"Scrape Error: {error_msg}")
        # Always return the error in a structured way instead of 400 
        # so the UI can handle it gracefully.
        return {
            "company_name": "Scrape Failed",
            "industry": "N/A",
            "about": f"Could not extract data from the website. Error: {error_msg}",
            "products": "N/A",
            "website": request.url,
            "socials": {
                "linkedin": "N/A",
                "twitter": "N/A",
                "facebook": "N/A",
                "instagram": "N/A",
                "youtube": "N/A"
            }
        }
    
    # AI Refinement
    try:
        refinement = await llm.refine_data(result["raw_text"], request.url, result.get("hints"))
        return refinement
    except Exception as e:
        print(f"AI Refinement Error: {e}")
        return {
            "company_name": "Refinement Failed",
            "industry": "N/A",
            "about": f"AI could not process the website content. Error: {str(e)}",
            "products": "N/A",
            "website": request.url,
            "socials": {
                "linkedin": "N/A",
                "twitter": "N/A",
                "facebook": "N/A",
                "instagram": "N/A",
                "youtube": "N/A"
            }
        }

@app.post("/bulk-scrape")
async def scrape_bulk(request: BulkScrapeRequest):
    # Limit to 20 for safety in one batch
    urls = request.urls[:20]
    
    async def process_one(url):
        data = await scraper.scrape_url(url)
        if data["status"] == "success":
            refined = await llm.refine_data(data["raw_text"], url, data.get("hints"))
            return refined
        else:
            return {
                "company_name": "Failed",
                "industry": "N/A",
                "about": f"Scrape Error: {data.get('error')}",
                "products": "N/A",
                "website": url,
                "socials": {
                    "linkedin": "N/A",
                    "twitter": "N/A",
                    "facebook": "N/A",
                    "instagram": "N/A",
                    "youtube": "N/A"
                }
            }

    results = await asyncio.gather(*(process_one(u) for u in urls))
    
    # Store or return the data
    return results

@app.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    # Read the file
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))
    
    # Assume the first column or column named "url" contains the URLs
    url_col = "url" if "url" in df.columns else df.columns[0]
    urls = df[url_col].tolist()
    
    # Procces as bulk
    results = await scrape_bulk(BulkScrapeRequest(urls=urls))
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
