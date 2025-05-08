import google.generativeai as genai
from pinecone import Pinecone
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Initialize clients
try:
    genai.configure(api_key=GOOGLE_API_KEY)
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)
except Exception as e:
    raise RuntimeError(f"Failed to initialize services: {str(e)}")

def search_pinecone(query: str, top_k: int = 10) -> List[Dict[str, Optional[str]]]:
    if not query or not isinstance(query, str):
        return []
    
    try:
        # Get embedding with proper error handling
        embedding = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"  # Lowercase as per current API
        ).get("embedding", [])
        
        if not embedding:
            print("Error: Empty embedding generated")
            return []

        # Query Pinecone with score threshold
        search_response = index.query(
            vector=embedding,
            top_k=top_k*3,  # Get extra results to filter
            include_metadata=True
        )

        # Filter and format results
        max_score = max([m['score'] for m in search_response['matches'] or [0]])
        threshold = max(0.5, max_score - 0.2)  # Adaptive threshold

        results = []
        for match in search_response['matches']:
            if match['score'] >= threshold:
                meta = match.get('metadata', {})
                results.append({
                    'name': meta.get('name', 'Unnamed'),
                    'url': meta.get('url', '#'),
                    'score': match['score'],
                    'type': meta.get('type', ''),
                    'duration': meta.get('duration', 0)
                })

        return sorted(results, key=lambda x: x['score'], reverse=True)[:top_k]

    except Exception as e:
        print(f"Search error: {str(e)}")
        return []