# verify_data.py
from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:@localhost:5432/postgres")

with engine.connect() as conn:
    # Count records
    result = conn.execute(text("SELECT COUNT(*) FROM appointment_management_system.conversation"))
    count = result.scalar()
    print(f"Total records: {count}")
    
    # Show all records
    result = conn.execute(text("SELECT * FROM appointment_management_system.conversation"))
    print("\nAll records:")
    for i, row in enumerate(result, 1):
        print(f"{i}. {dict(row._mapping)}")