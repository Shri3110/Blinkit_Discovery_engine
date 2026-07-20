import chromadb
import os

# Define the path where ChromaDB will persist data locally
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'chroma_data')

class VectorStore:
    def __init__(self, collection_name="reviews"):
        # Initialize a persistent ChromaDB client
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        
        # Get or create the collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity for text embeddings
        )
        print(f"Connected to ChromaDB collection: '{collection_name}'")

    def add_reviews(self, ids: list[str], documents: list[str], metadatas: list[dict]):
        """
        Adds text documents to the ChromaDB collection.
        Embeddings will be generated automatically by Chroma's default embedding function
        if you don't pass an explicit embedding function (uses all-MiniLM-L6-v2).
        """
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        print(f"Added {len(ids)} documents to the vector store.")

    def search_reviews(self, query: str, n_results: int = 5):
        """
        Search for similar reviews using a text query.
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results

if __name__ == "__main__":
    # Test Vector Store locally
    vs = VectorStore()
    
    # Add dummy data to test
    vs.add_reviews(
        ids=["rev_1", "rev_2"],
        documents=[
            "I love the fast 10-minute delivery, it's so convenient!",
            "The app is difficult to navigate when searching for pet food."
        ],
        metadatas=[
            {"source": "App Store", "sentiment": "positive"},
            {"source": "Google Play", "sentiment": "negative"}
        ]
    )
    
    # Search dummy data
    search_res = vs.search_reviews("How is the delivery speed?", n_results=1)
    print("Search Results:", search_res)
