import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from src.db.database import SessionLocal
from src.db.models import ProcessedData

# Same lightweight embedding model as vector_store.py
default_ef = embedding_functions.DefaultEmbeddingFunction()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")

def query_discovery_engine(question: str, top_k: int = 5):
    if not GROQ_API_KEY:
        raise ValueError("No GROQ_API_KEY found in .env")
        
    print(f"Querying Discovery Engine: '{question}'")
    
    # Connect to ChromaDB
    chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name="reviews_collection", embedding_function=default_ef)
    
    # Semantic Search
    results = collection.query(
        query_texts=[question],
        n_results=top_k
    )
    
    if not results['documents'] or not results['documents'][0]:
        return "No relevant insights found in the database."
        
    retrieved_docs = results['documents'][0]
    metadata_list = results['metadatas'][0]
    
    # We could also fetch user segments from the SQLite DB if needed,
    # but the normalized content is already in ChromaDB!
    
    # Construct Context
    context_blocks = []
    evidence = []
    for i, doc in enumerate(retrieved_docs):
        context_blocks.append(f"- {doc}")
        evidence.append({
            "id": metadata_list[i].get("id"),
            "content": doc,
            "segment": metadata_list[i].get("segment", "Unknown"),
            "topic": metadata_list[i].get("topic", "None")
        })
        
    context_str = "\n".join(context_blocks)
    
    # Ask LLM to synthesize
    system_prompt = """
    You are an expert AI Product Manager for Blinkit (a quick commerce app).
    Analyze the provided user contexts to answer the PM's question.
    Structure your answer as an actionable Product Insight Report.
    Use clear headings, bullet points, and directly quote insights to support your conclusions.
    Focus exclusively on answering the user's prompt based on the context provided.
    
    IMPORTANT: Do NOT use asterisks (*) or markdown formatting for bold/italics anywhere in your response. 
    Use plain text or standard numbered/bulleted lists using dashes (-). Do not include asterisks.
    Do NOT use the word "feedback" in your response (e.g. do not use "Feedback 1", "Feedback 2").
    Do NOT use phrases like "Evidence used" or "Evidence:" in your response. Just present the insights naturally.
    """
    
    user_prompt = f"Product Question: {question}\n\nContext:\n{context_str}"
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=1500,
    )
    
    raw_content = response.choices[0].message.content.strip()
    
    # Robust post-processing to guarantee absolutely no asterisks are returned to the UI
    # Also removing bullet point dashes (- ) as requested, while preserving hyphenated words
    clean_content = raw_content.replace('*', '').replace('- ', '')
    
    return {
        "report": clean_content,
        "evidence": evidence
    }

if __name__ == "__main__":
    # Test Question based on Blinkit case study
    test_question = "Why do users hesitate to purchase high-value items or electronics from us?"
    result = query_discovery_engine(test_question)
    print("Report:", result["report"])
    print("Evidence Count:", len(result["evidence"]))
