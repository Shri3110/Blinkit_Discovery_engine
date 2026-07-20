from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func
from src.db.database import SessionLocal
from src.db.models import ProcessedData, RawData
from src.engine.rag_pipeline import query_discovery_engine

app = FastAPI(title="Blinkit AI Discovery Engine API")

# Allow CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/api/stats")
def get_stats():
    db = SessionLocal()
    try:
        total_raw = db.query(RawData).count()
        total_processed = db.query(ProcessedData).count()
        
        # Get top segments
        segments = db.query(
            ProcessedData.user_segment, 
            func.count(ProcessedData.id).label('count')
        ).group_by(ProcessedData.user_segment).all()
        
        return {
            "total_reviews": total_raw,
            "processed_reviews": total_processed,
            "segments": [{"name": s[0], "value": s[1]} for s in segments if s[0]]
        }
    finally:
        db.close()

@app.get("/api/reviews")
def get_reviews(limit: int = 50):
    db = SessionLocal()
    try:
        reviews = db.query(ProcessedData).order_by(ProcessedData.created_at.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "content": r.normalized_content,
                "segment": r.user_segment,
                "topics": r.topic_tags
            } for r in reviews
        ]
    finally:
        db.close()

@app.get("/api/trends/heatmap")
def get_heatmap():
    db = SessionLocal()
    try:
        reviews = db.query(ProcessedData).all()
        heatmap = {}
        for r in reviews:
            segment = r.user_segment or "Unknown"
            if segment not in heatmap:
                heatmap[segment] = {}
            for topic in (r.topic_tags or []):
                if topic not in heatmap[segment]:
                    heatmap[segment][topic] = 0
                heatmap[segment][topic] += 1
                
        formatted_data = []
        for segment, topics in heatmap.items():
            row = {"segment": segment}
            row.update(topics)
            formatted_data.append(row)
            
        return formatted_data
    finally:
        db.close()

@app.post("/api/query")
def run_query(request: QueryRequest):
    try:
        if not request.query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
            
        result = query_discovery_engine(request.query, top_k=5)
        if isinstance(result, str):
            return {"report": result, "evidence": []}
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
