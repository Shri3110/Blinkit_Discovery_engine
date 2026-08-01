import sys, os
from groq import Groq
sys.path.append(os.getcwd())
from src.db.database import SessionLocal
from src.db.models import RawData

def generate(question, context):
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY") or os.getenv("GROQ_ID"))
    system_prompt = """
    You are an expert deterministic AI Product Manager for Blinkit.
    Analyze the provided user contexts to answer the PM's question.
    
    STRICT RAG GROUNDING RULES:
    1. Answer ONLY using the information explicitly present in the retrieved review context.
    2. NEVER use your pretrained knowledge or outside information.
    3. NEVER fabricate or hallucinate insights.
    4. Every insight and recommendation must be directly supported by the retrieved reviews.
    5. If the provided context does not contain sufficient evidence, you MUST explicitly return exactly: "Insufficient evidence found in the retrieved reviews."
    
    Structure your answer as a highly concise Product Insight Report.
    Use EXACTLY the following headings (omit any that are completely irrelevant):
    - Key Findings
    - Pain Points
    - Product Opportunities
    - Recommended Actions
    """
    user_prompt = f"Product Question: {question}\n\nContext:\n{context}"
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        max_tokens=1500,
    )
    return response.choices[0].message.content.strip()

def run():
    db = SessionLocal()

    questions_and_keywords = [
        ("What prevents users from exploring new categories?", ['prevent', 'hesitat', 'scared', 'afraid', 'explor', 'new categor']),
        ("What information do users need before trying a new category?", ['information', 'details', 'trying', 'new categor', 'know']),
        ("Which user segments are more likely to experiment?", ['experiment', 'segment', 'trying', 'new categor'])
    ]

    with open('synthesis_report_missing.md', 'w') as f:
        for q, kws in questions_and_keywords:
            print(f"Processing: {q}")
            reviews = []
            for kw in kws:
                matches = db.query(RawData).filter(RawData.content.ilike(f'%{kw}%')).limit(20).all()
                for m in matches:
                    if m.content not in reviews:
                        reviews.append(m.content)
            
            context = "\n---\n".join(reviews[:40])
            print(f"Found {len(reviews)} reviews for context")
            if not reviews:
                f.write(f"## {q}\n\nInsufficient evidence found in the retrieved reviews.\n\n")
                continue
                
            res = generate(q, context)
            clean_res = res.replace('*', '')
            f.write(f"## {q}\n\n{clean_res}\n\n")

if __name__ == '__main__':
    run()
