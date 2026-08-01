import sys, os
sys.path.append(os.getcwd())
from src.engine.rag_pipeline import query_discovery_engine

def run():
    print("Loading questions...")
    with open('questions.txt', 'r', encoding='utf-8') as f:
        questions = [q.strip() for q in f if q.strip()]

    print("Generating report...")
    with open('synthesis_report.md', 'w', encoding='utf-8') as f:
        f.write('# User Review Synthesis Report\n\n')
        for q in questions:
            print(f'Processing: {q}')
            try:
                res = query_discovery_engine(q)
                f.write(f'## {q}\n\n')
                f.write(res['report'] + '\n\n')
            except Exception as e:
                print(f'Error processing {q}: {e}')
                f.write(f'## {q}\n\nError: {e}\n\n')
    print('Done!')

if __name__ == "__main__":
    run()
