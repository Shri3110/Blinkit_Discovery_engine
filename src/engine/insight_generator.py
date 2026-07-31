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
    
    # Increase n_results to retrieve enough highly relevant review chunks
    results = collection.query(
        query_texts=[query],
        n_results=max(n_results, 20)
    )
    
    documents = results['documents'][0]
    
    if 'distances' in results and results['distances']:
        distances = results['distances'][0]
        # Rank by semantic similarity and ignore low-confidence matches (distance > 1.5)
        documents = [doc for doc, dist in zip(documents, distances) if dist < 1.5]
    
    if not documents:
        return "Insufficient evidence found in the retrieved reviews."
        
    context = "\n---\n".join(documents)
    
    # 2. Synthesize with Groq
    print("Synthesizing insight with Groq...")
    system_prompt = """
    You are a deterministic Product Intelligence AI for Blinkit.
    Your sole purpose is to synthesize actionable product insights from the provided user reviews.
    
    STRICT RAG GROUNDING RULES:
    1. Answer ONLY using the information explicitly present in the retrieved review context.
    2. NEVER use your pretrained knowledge or outside information.
    3. NEVER fabricate or hallucinate insights, statistics, percentages, review counts, personas, or product opportunities.
    4. Every insight and recommendation must be directly supported by the retrieved reviews. Do not make assumptions or speculative conclusions.
    5. If the provided context does not contain sufficient evidence to answer the query, you MUST explicitly return exactly: "Insufficient evidence found in the retrieved reviews."
    
    FORMATTING RULES:
    1. Do NOT use the word "feedback" in your response (e.g. do not use "Feedback 1", "Feedback 2").
    2. Do NOT use phrases like "Evidence used" or "Evidence:" in your response. Just present the insights naturally.
    """
    
    groq_client = Groq(api_key=GROQ_API_KEY)
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"Query: {query}\n\nContext:\n{context}"}
        ],
        model="llama-3.1-8b-instant",
        temperature=0.0,
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
