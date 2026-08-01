import sys, os
sys.path.append(os.getcwd())
from src.engine.rag_pipeline import get_embedding_model
from pinecone import Pinecone

def run():
    api_key = os.getenv('PINECONE_API_KEY')
    pc = Pinecone(api_key=api_key)
    index = pc.Index('blinkit1')
    model = get_embedding_model()

    questions = [
        "What prevents users from exploring new categories?",
        "What information do users need before trying a new category?",
        "Which user segments are more likely to experiment?"
    ]

    for q in questions:
        print(f"\n--- {q} ---")
        emb = list(model.embed([q]))[0].tolist()
        res = index.query(vector=emb, top_k=5, include_metadata=True)
        for m in res.matches:
            text = m.metadata.get('text', '')[:100].replace('\n', ' ')
            print(f"Score: {m.score:.3f} | {text}")

if __name__ == '__main__':
    run()
