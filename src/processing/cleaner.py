import re
import spacy

# Load spaCy English model (ensure you have run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Warning: spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    nlp = None

def clean_text(text: str) -> str:
    """
    Normalizes and cleans unstructured user feedback.
    """
    if not isinstance(text, str):
        return ""

    # Lowercase the text
    text = text.lower()

    # Remove URLs
    text = re.sub(r"http\S+|www\S+|https\S+", '', text, flags=re.MULTILINE)

    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)

    # Remove special characters and numbers (keeping only letters and spaces)
    text = re.sub(r'[^a-zA-Z\s]', '', text)

    # Remove extra whitespace
    text = " ".join(text.split())

    return text

def lemmatize_text(text: str) -> str:
    """
    Uses spaCy to lemmatize text and remove stop words.
    """
    if not nlp:
        return text # Fallback to just cleaned text if model isn't loaded

    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

def process_review(raw_review: str) -> str:
    """
    Full pipeline to process a raw review.
    """
    cleaned = clean_text(raw_review)
    processed = lemmatize_text(cleaned)
    return processed

if __name__ == "__main__":
    # Test the cleaner pipeline
    sample_review = "I LOVED the delivery from Blinkit today!!! It arrived in 10 mins. Very fast service. Check it out at https://blinkit.com/ <br> 123"
    print("Original:", sample_review)
    print("Cleaned:", clean_text(sample_review))
    print("Processed:", process_review(sample_review))
