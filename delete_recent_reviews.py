import os
from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres.hxmuejleyyrtdrrmzhje:Shriram%40311096@aws-1-ap-south-1.pooler.supabase.com:6543/postgres')

def run_cleanup():
    with engine.connect() as conn:
        total = conn.execute(text('SELECT COUNT(*) FROM raw_data')).scalar()
        target = 4650
        diff = total - target
        if diff > 0:
            print(f"Current total is {total}. Deleting {diff} most recent records to get back to {target}...")
            
            # Fetch the IDs of the most recent `diff` records
            ids_to_delete_result = conn.execute(text(f'SELECT id FROM raw_data ORDER BY id DESC LIMIT {diff}')).fetchall()
            ids_to_delete = [r[0] for r in ids_to_delete_result]
            
            if ids_to_delete:
                id_tuple = tuple(ids_to_delete)
                if len(id_tuple) == 1:
                    # formatted as (123) not (123,) for postgres IN clause if needed, but parameter binding is better
                    pass
                
                # Using parameters for safety
                id_placeholders = ', '.join([f':id_{i}' for i in range(len(ids_to_delete))])
                params = {f'id_{i}': id_val for i, id_val in enumerate(ids_to_delete)}
                
                print("Deleting processed_data...")
                conn.execute(text(f'DELETE FROM processed_data WHERE raw_data_id IN ({id_placeholders})'), params)
                
                print("Deleting raw_data...")
                conn.execute(text(f'DELETE FROM raw_data WHERE id IN ({id_placeholders})'), params)
                
                conn.commit()
                print("Deleted successfully. Verifying new total...")
                new_total = conn.execute(text('SELECT COUNT(*) FROM raw_data')).scalar()
                print(f"New total: {new_total}")
        else:
            print(f"Total is {total}, which is already {target} or less. No deletion needed.")

if __name__ == '__main__':
    run_cleanup()
