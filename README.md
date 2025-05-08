# SHL Assessment Recommendation Engine

This project builds a semantic search engine that recommends SHL assessments based on user queries, using LLM embeddings and vector similarity.

## Features

- Web scraping of SHL product catalog
- Gemini API for embedding text (job queries and assessment metadata)
- Pinecone vector database for fast semantic search
- FastAPI backend with `/recommend` endpoint
- Optional Streamlit UI for testing recommendations
- Evaluation using Recall@3 and MAP@3

## Tech Stack

- Python 3.11
- FastAPI
- Gemini (Google Generative AI API)
- Pinecone (serverless)
- Pandas, NumPy
- Streamlit (optional UI)
- Docker (for deployment)

## How It Works

1. Scrapes SHL's public product catalog
2. Generates text embeddings using Gemini
3. Stores assessment vectors and metadata in Pinecone
4. When a user submits a query:
   - The query is embedded via Gemini
   - Compared with stored vectors using Pinecone
   - Returns top 3 most relevant assessments
5. Evaluation metrics are computed against labeled queries

## Setup Instructions

### Environment Variables

Create a `.env` file with:

```env
GOOGLE_API_KEY=your_gemini_api_key
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENV=pinecone_env
PINECONE_INDEX_NAME=index_name
# shl_recommendation_engine
