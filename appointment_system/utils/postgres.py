import psycopg2
from psycopg2.extras import RealDictCursor
import os

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="",
        options="-c search_path=appointment_management_system,public"
    )
