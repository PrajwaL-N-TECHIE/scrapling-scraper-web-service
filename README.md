# AI-Powered Lead Intelligence Scraper

A modern, high-performance web scraper designed for B2B lead generation. This tool extracts company overviews, industry classification, and product offerings directly from websites using **Scrapling** and **Groq (Llama 3.3)**.

## 🚀 Features

- **Blazing Fast Extraction**: Uses `AsyncFetcher` for concurrent, non-blocking page loads.
- **AI-Powered Refinement**: Leverages Llama 3.3 to transform raw HTML into structured, high-quality company profiles.
- **Clean UI**: A sleek React (Vite) dashboard for single URL analysis and batch processing.
- **Privacy First**: Automatically filters out personal contact details to focus on core company data.
- **Scalable**: Handles bulk URL lists and CSV uploads with ease.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Scrapling, Groq SDK, Pandas.
- **Frontend**: React, Framer Motion, Lucide Icons, Axios, Vite.
- **AI Model**: `llama-3.1-8b-instant` (optimized for speed and accuracy).

## 🏃 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API Key

### Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/prajwal-infynd/web-scraper-scrapling.git
   cd web-scraper-scrapling
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   # Create a .env file with:
   # GROQ_API_KEY=your_key_here
   # MODEL_NAME=llama-3.1-8b-instant
   uvicorn main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

## 📁 Project Structure

- `/backend`: FastAPI server and scraper logic.
- `/frontend`: Vite-powered React application.

## 📄 License
MIT
