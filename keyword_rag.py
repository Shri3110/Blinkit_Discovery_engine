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
