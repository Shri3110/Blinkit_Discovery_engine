import sys, os
sys.path.append(os.getcwd())
from src.db.database import SessionLocal
from src.db.models import RawData

def run():
    db = SessionLocal()
    keywords = ['prevent', 'hesitat', 'explor', 'trying', 'scared', 'afraid', 'information', 'details', 'experiment', 'new categor']
    for kw in keywords:
        count = db.query(RawData).filter(RawData.content.ilike(f'%{kw}%')).count()
        print(f"Keyword '{kw}': {count} reviews")

if __name__ == '__main__':
    run()
