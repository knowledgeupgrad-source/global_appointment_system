# test_db.py
from appointment_system.utils.postgres import AppointmentDB, engine
from appointment_system.services.conversation import Conversation
from datetime import datetime, UTC
from sqlalchemy import text

print("=== Starting Test ===\n")

session = AppointmentDB.get_session()
try:
    # Create test record
    test_id = "test_" + str(datetime.now().timestamp())
    test_conv = Conversation(
        conversation_id=test_id,
        end_user_id="test_user",
        input_message="Hello from test",
        response_from="test",
        create_at=datetime.now(UTC),
        handled_by_admin=False
    )
    
    session.add(test_conv)
    session.flush()  # Force write to DB
    print(f"✓ Flushed to database")
    
    session.commit()  # Commit transaction
    print(f"✓ Committed transaction")
    
    # Verify in same session
    count_in_session = session.query(Conversation).count()
    print(f"✓ Count in same session: {count_in_session}")
    
except Exception as e:
    session.rollback()
    print(f"✗ Error during save: {e}")
    import traceback
    traceback.print_exc()
finally:
    session.close()
    print("✓ Session closed\n")

# NOW verify with a completely new connection
print("=== Verifying with Raw SQL ===\n")
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM appointment_management_system.conversation"))
    count = result.scalar()
    print(f"Total records (raw SQL): {count}")
    
    if count > 0:
        result = conn.execute(text("SELECT * FROM appointment_management_system.conversation ORDER BY create_at DESC LIMIT 5"))
        print("\nLast 5 records:")
        for row in result:
            print(f"  - ID: {row.conversation_id}, Message: {row.input_message}")
    else:
        print("⚠️  NO RECORDS FOUND!")

print("\n=== Test Complete ===")