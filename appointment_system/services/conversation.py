from sqlalchemy import Column, String, Boolean, DateTime, text
from appointment_system.utils.postgres import Base, engine

class Conversation(Base):
    __tablename__ = "conversation"
    __table_args__ = {"schema": "appointment_management_system"}

    conversation_id = Column(String, primary_key=True)
    end_user_id = Column(String)
    end_user_mobile_number = Column(String)
    input_message = Column(String)
    response_from = Column(String)
    output_message = Column(String)
    handled_by_admin = Column(Boolean, default=False)
    create_at = Column(DateTime)

# Create schema and tables - FIXED: Use text()
with engine.connect() as conn:
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS appointment_management_system"))
    conn.commit()

Base.metadata.create_all(engine)