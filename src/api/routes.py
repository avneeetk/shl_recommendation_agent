from fastapi import APIRouter, Request
from src.core.recommender import search_pinecone

router = APIRouter()

@router.post("/recommend")
async def recommend(request: Request):
    try:
        body = await request.json()
        query_text = body.get("query", "").strip()
        if not query_text:
            return {"error": "Query is required."}

        results = search_pinecone(query_text, top_k=3)
        return {"results": results}
    
    except Exception as e:
        return {"error": str(e)}