from scrapling import AsyncFetcher
import asyncio
import re
from typing import Dict, List, Set, Optional

class ScraperService:
    MAILTO = "mailto:"
    TEL = "tel:"

    def __init__(self):
        # Using a realistic User-Agent to avoid being blocked as a bot
        self.fetcher = AsyncFetcher(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        self.email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # More robust phone regex to capture full numbers
        self.phone_regex = re.compile(r'(\+?\d{1,4}[-.\s]?)?(\(?\d{1,4}\)?[-.\s]?)?[\d\s\-.]{7,18}')
        # Simple address-like regex to help the LLM (capturing postal codes and road names)
        self.address_regex = re.compile(r'[\d]{1,5}\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:,\s[A-Z][a-z0-9\s,]+){2,}')

    def _is_social(self, l_lower: str) -> Optional[str]:
        mapping = {
            "linkedin.com/": "linkedin",
            "twitter.com/": "twitter",
            "x.com/": "twitter",
            "facebook.com/": "facebook",
            "instagram.com/": "instagram",
            "youtube.com/": "youtube"
        }
        for domain, key in mapping.items():
            if domain in l_lower:
                return key
        return None

    def _extract_contact_hints(self, text: str, html_links: List[str]) -> Dict[str, Set[str]]:
        """Extracts emails, phones, and addresses using regex and link harvesting."""
        hints = {"emails": set(), "phones": set(), "addresses": set()}
        
        hints["emails"].update(self.email_regex.findall(text))
        hints["phones"].update(self.phone_regex.findall(text))
        hints["addresses"].update(self.address_regex.findall(text))

        for link in html_links:
            if link.startswith(self.MAILTO):
                email = link.replace(self.MAILTO, '').split('?')[0].strip()
                if email: hints["emails"].add(email)
            elif link.startswith(self.TEL):
                phone = link.replace(self.TEL, '').strip()
                if phone: hints["phones"].add(phone)
                
        return hints

    def _extract_links(self, response):
        """Extracts and prioritizes links for deeper analysis."""
        links = response.css('a::attr(href)').getall()
        base_url = str(response.url).rstrip('/')
        
        discovery = {
            "about": None, "contact": None, "all_links": [],
            "socials": dict.fromkeys(["linkedin", "twitter", "facebook", "instagram", "youtube"])
        }
        
        for link in links:
            if not link: continue
            discovery["all_links"].append(link)
            
            # Normalize
            full_link = link
            if link.startswith('//'): full_link = f"https:{link}"
            elif link.startswith('/'): full_link = f"{base_url}{link}"
            elif not link.startswith('http') and not link.startswith((self.MAILTO, self.TEL)):
                full_link = f"{base_url}/{link}"
                
            l_lower = link.lower()
            
            # Sub-pages
            if not discovery["about"] and any(x in l_lower for x in ["about", "company"]):
                discovery["about"] = full_link
            if not discovery["contact"] and any(x in l_lower for x in ["contact", "support", "get-in-touch", "location"]):
                discovery["contact"] = full_link
                
            # Socials
            social_key = self._is_social(l_lower)
            if social_key and not discovery["socials"][social_key]:
                discovery["socials"][social_key] = full_link
                
        return discovery

    async def _fetch_page_text(self, url: str) -> str:
        """Helper to fetch and clean text from a single page."""
        try:
            resp = await self.fetcher.get(url, timeout=15)
            if resp.status == 200:
                chunks = resp.css('body *::text').getall()
                return " ".join([t.strip() for t in chunks if t.strip()])
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        return ""

    async def scrape_url(self, url: str, deep: bool = False):
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"

        try:
            # 1. HOME PAGE SCRAPE
            response = await self.fetcher.get(url, timeout=20)
            
            if response.status != 200:
                return {"url": url, "status": "error", "error": f"Status {response.status}"}
            
            discovery = self._extract_links(response)
            
            # Extract content from homepage
            text_chunks = response.css('body *::text').getall()
            main_text = " ".join([t.strip() for t in text_chunks if t.strip()]) or response.text[:5000]
            
            # Aggressively capture footer/bottom text
            footer_text = " ".join(response.css('footer *::text, [id*="footer"] *::text, [class*="footer"] *::text').getall())
            main_text += f"\n\nEXPLICIT FOOTER CONTENT:\n{footer_text}"

            # Final hints from combined text
            hints = self._extract_contact_hints(main_text, discovery["all_links"])
            
            # 2. DEEP RESEARCH (Visit About AND Contact concurrently)
            targets = []
            if discovery["about"]: targets.append(discovery["about"])
            if discovery["contact"]: targets.append(discovery["contact"])
            
            # Deduplicate and remove home URL
            targets = list(set([t for t in targets if t.rstrip('/') != url.rstrip('/')]))
            
            if targets:
                print(f"Deep Researching for {url}: {targets}")
                pages_content = await asyncio.gather(*[self._fetch_page_text(t) for t in targets])
                for i, content in enumerate(pages_content):
                    if content:
                        main_text += f"\n\nRESEARCH CONTENT FROM {targets[i]}:\n" + content[:15000]
                        sub_hints = self._extract_contact_hints(content, []) 
                        hints["emails"].update(sub_hints["emails"])
                        hints["phones"].update(sub_hints["phones"])
                        hints["addresses"].update(sub_hints["addresses"])

            print(f">>> Found Data for {url}")

            return {
                "url": url,
                "status": "success",
                "raw_text": main_text[:60000], 
                "title": response.css('title::text').get() or "No Title",
                "socials": discovery["socials"]
            }
        except Exception as e:
            return {"url": url, "status": "error", "error": str(e)}
