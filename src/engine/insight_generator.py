import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

# Reuse the same default embedding function as the vector store
default_ef = embedding_functions.DefaultEmbeddingFunction()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID")

def generate_insight(query: str, n_results: int = 10):
    """
    RAG Pipeline:
    1. Query ChromaDB for reviews matching the query.
    2. Pass the reviews to Groq LLM to synthesize an insight.
    """
    if not GROQ_API_KEY:
        raise ValueError("No GROQ_API_KEY found in .env")

    print(f"Retrieving context for query: '{query}'")
    
    # 1. Retrieve from ChromaDB
    chroma_path = os.getenv("CHROMA_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db"))
    client = chromadb.PersistentClient(path=chroma_path)
    
    collection = client.get_collection(
        name="reviews_collection",
        embedding_function=default_ef
    )
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    documents = results['documents'][0]
    
    if not documents:
        return "No relevant context found to answer the query."
        
    context = "\n---\n".join(documents)
    
    # 2. Synthesize with Groq
    print("Synthesizing insight with Groq...")
    system_prompt = """
    You are an AI Product Manager Assistant for Blinkit.
    You will be provided with user insights retrieved from a vector database based on a specific query.
    Synthesize the insights to answer the user's query. 
    Provide actionable product insights, highlighting user pain points or cross-category opportunities.
    Use insights from the provided context to support your claims.
    
    IMPORTANT INSTRUCTIONS:
    1. Do NOT use the word "feedback" in your response (e.g. do not use "Feedback 1", "Feedback 2").
    2. Do NOT use phrases like "Evidence used" or "Evidence:" in your response. Just present the insights naturally.
    """
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nContext:\n{context}"}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.3,
        max_tokens=500
    )
    
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    # Test the RAG pipeline
    test_query = "What prevents users from exploring new product categories on Blinkit?"
    try:
        insight = generate_insight(test_query)
        print("\n--- AI-Generated Insight ---\n")
        print(insight)
    except Exception as e:
        print(f"Error generating insight: {e}")
