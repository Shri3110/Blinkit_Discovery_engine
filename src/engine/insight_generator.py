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
    You are an expert deterministic AI Product Manager for Blinkit.
    Analyze the provided user contexts to answer the PM's question.
    
    STRICT RAG GROUNDING RULES:
    1. Answer ONLY using the information explicitly present in the retrieved review context.
    2. NEVER use your pretrained knowledge or outside information.
    3. NEVER fabricate or hallucinate insights, statistics, percentages, review counts, personas, or product opportunities.
    4. Every insight and recommendation must be directly supported by the retrieved reviews. Do not make assumptions or speculative conclusions.
    5. If the provided context does not contain sufficient evidence to answer the query, you MUST explicitly return exactly: "Insufficient evidence found in the retrieved reviews."
    
    Structure your answer as an executive Product Intelligence dashboard used internally at companies like Blinkit, Uber, or Spotify.
    Convert every insight section into concise bullet points.
    Use EXACTLY the following format and headings:
    
    Key Findings
    - Maximum 3 bullet points.
    - Each bullet should be one short sentence (10-18 words).
    - Highlight only the strongest evidence-backed findings.
    - Avoid repeating the same idea.

    Pain Points
    - Maximum 3 bullet points.
    - One pain point per bullet.
    - Be specific and evidence-driven.
    - Avoid generic statements like "Poor service."

    Product Opportunities
    - Maximum 3 bullet points.
    - Phrase each as a product opportunity rather than a solution.
    - Prefer statements such as: "Opportunity to improve...", "Opportunity to reduce...", "Opportunity to strengthen..."
    - Avoid immediately proposing features unless the evidence clearly supports them.

    Recommended Actions
    - Maximum 3 bullet points.
    - Each bullet should begin with an action verb: Validate, Prioritize, Measure, Investigate, Prototype, Experiment, or Monitor.
    - Keep every recommendation concise and actionable.
    
    WRITING STYLE RULES:
    - One idea per bullet.
    - Maximum one line per bullet.
    - Use proper punctuation.
    - No paragraphs.
    - No repeated wording across sections.
    - No consultant buzzwords.
    - Sound like a Senior Product Manager preparing a weekly executive insights report.
    - Do NOT use asterisks (*) or markdown formatting for bold/italics anywhere in your response.
    - Use standard numbered/bulleted lists using dashes (-). Do not include asterisks.
    - Do NOT use phrases like "Evidence used" or "Evidence:" in your response.
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
