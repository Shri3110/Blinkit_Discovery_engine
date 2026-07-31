import os
from pinecone import Pinecone
from groq import Groq
from src.db.database import SessionLocal
from src.db.models import ProcessedData, RawData

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")

_model = None
def get_embedding_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding
        _model = TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2')
    return _model

def query_discovery_engine(question: str, top_k: int = 5):
    if not GROQ_API_KEY:
        raise ValueError("No GROQ_API_KEY found in .env")
        
    print(f"Querying Discovery Engine: '{question}'")
    
    # Generate query embedding
    model = get_embedding_model()
    query_embedding = list(model.embed([question]))[0].tolist()
    
    # Connect to Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("No PINECONE_API_KEY found in .env")
        
    pc = Pinecone(api_key=api_key)
    index_name = "blinkit1"
    index = pc.Index(index_name)
    
    # Semantic Search
    results = index.query(
        vector=query_embedding,
        top_k=max(top_k, 20),
        include_metadata=True
    )
    
    matches = [m for m in results.matches if m.score > 0.3]
    
    if not matches:
        return {
            "report": "Insufficient evidence found in the retrieved reviews.",
            "evidence": []
        }
        
    db = SessionLocal()
    evidence = []
    context_blocks = []
    source_distribution = {}
    supporting_review_count = 0
    
    try:
        raw_data_ids = [match.metadata.get("raw_data_id") for match in matches if match.metadata and match.metadata.get("raw_data_id")]
        
        processed_records = {r.raw_data_id: r for r in db.query(ProcessedData).filter(ProcessedData.raw_data_id.in_(raw_data_ids)).all()}
        raw_records = {r.id: r for r in db.query(RawData).filter(RawData.id.in_(raw_data_ids)).all()}
        
        for i, match in enumerate(matches):
            doc = match.metadata.get("text", "")
            context_blocks.append(f"- {doc}")
            
            raw_id = match.metadata.get("raw_data_id")
            
            segment = "Unknown"
            topic = "None"
            source = "Unknown"
            
            if raw_id:
                if raw_id in processed_records:
                    segment = processed_records[raw_id].user_segment or "Unknown"
                    topics = processed_records[raw_id].topic_tags
                    topic = topics[0] if topics else "None"
                
                if raw_id in raw_records:
                    source = raw_records[raw_id].source or "Unknown"
                    source_distribution[source] = source_distribution.get(source, 0) + 1
            
            evidence.append({
                "id": raw_id or match.id,
                "content": doc,
                "segment": segment,
                "topic": topic
            })
            
        # Get broader supporting count (Pinecone returns similarity score usually between 0 and 1)
        broader_results = index.query(
            vector=query_embedding,
            top_k=50,
            include_metadata=False
        )
        supporting_review_count = sum(1 for match in broader_results.matches if match.score > 0.3)
        if supporting_review_count < len(matches):
            supporting_review_count = len(matches)
            
        scores = [match.score for match in matches]
        avg_score = sum(scores) / len(scores) if scores else 0
        confidence_score = max(0, min(100, int(avg_score * 100)))
            
    finally:
        db.close()
        
    context_str = "\n".join(context_blocks)
    
    # Ask LLM to synthesize
    system_prompt = """
    You are an expert deterministic AI Product Manager for Blinkit.
    Analyze the provided user contexts to answer the PM's question.
    
    STRICT RAG GROUNDING RULES:
    1. Answer ONLY using the information explicitly present in the retrieved review context.
    2. NEVER use your pretrained knowledge or outside information.
    3. NEVER fabricate or hallucinate insights, statistics, percentages, review counts, personas, or product opportunities.
    4. Every insight and recommendation must be directly supported by the retrieved reviews. Do not make assumptions or speculative conclusions.
    5. If the provided context does not contain sufficient evidence to answer the query, you MUST explicitly return exactly: "Insufficient evidence found in the retrieved reviews."
    
    Structure your answer as a highly concise Product Insight Report.
    Use EXACTLY the following headings (omit any that are completely irrelevant):
    - Key Findings
    - Pain Points
    - Product Opportunities
    - Recommended Actions

    IMPORTANT GUIDELINES:
    - Avoid vague generalizations. Be extremely specific.
    - Directly reference exact scenarios, item types, or issues mentioned in the context.
    - Provide highly actionable Product Opportunities and Recommended Actions that an engineering/design team could actually build.
    - Keep explanations punchy and data-driven. Use max 2 bullet points per section.
    
    FORMATTING RULES:
    - Do NOT use asterisks (*) or markdown formatting for bold/italics anywhere in your response.
    - Use standard numbered/bulleted lists using dashes (-). Do not include asterisks.
    - Do NOT use phrases like "Evidence used" or "Evidence:" in your response.
    """
    
    user_prompt = f"Product Question: {question}\n\nContext:\n{context_str}"
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        max_tokens=1500,
    )
    
    raw_content = response.choices[0].message.content.strip()
    
    if "Insufficient evidence" in raw_content:
        return {
            "report": "Insufficient evidence found in the retrieved reviews.",
            "evidence": []
        }
        
    clean_content = raw_content.replace('*', '').replace('- ', '')
    
    source_dist_str = ", ".join([f"{k}: {v}" for k, v in source_distribution.items()])
    
    evidence_layer_text = (
        f"\n\n--- Evidence Layer ---\n"
        f"Evidence Count: {len(matches)}\n"
        f"Confidence Score: {confidence_score}%\n"
        f"Source Distribution: {source_dist_str}\n"
        f"Supporting Review Count: {supporting_review_count}\n"
    )
    
    return {
        "report": clean_content + evidence_layer_text,
        "evidence": evidence
    }

if __name__ == "__main__":
    test_question = "Why do users hesitate to purchase high-value items or electronics from us?"
    result = query_discovery_engine(test_question)
    print("Report:", result["report"])
    print("Evidence Count:", len(result["evidence"]))
