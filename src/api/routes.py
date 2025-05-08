from fastapi import APIRouter, Request
from src.core.recommender import search_pinecone

router = APIRouter()

@router.post("/recommend")
async def recommend(request: Request):
    try:
        body = await request.json()
        query_text = body.get("query", "").strip()
        if not query_text:
            return {"results":[]}

        results = search_pinecone(query_text, top_k=3)
        return {"results": results or []}

    except Exception as e:
        print(f"API Error: {str(e)}")
        return {"results": []}