import psycopg2
from .postgres import get_connection
from .logger import logger

def get_values(table, columns=None, where=None, schema=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        col_str = ", ".join(columns) if columns else "*"
        
        query = f"SELECT {col_str} FROM {schema}.{table}"
        params = []
        
        if where:
            conditions = " AND ".join([f"{k} = %s" for k in where.keys()])
            query += f" WHERE {conditions}"
            params = list(where.values())
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(results)} rows from {table}")
        return results
    
    except Exception as e:
        logger.error(f"Error getting values: {e}")
        return []


def save_values(table, data, schema="public"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        columns = list(data.keys())
        values = list(data.values())
        
        col_str = ", ".join(columns)
        placeholder = ", ".join(["%s"] * len(columns))
        
        query = f"INSERT INTO {schema}.{table} ({col_str}) VALUES ({placeholder})"
        
        cursor.execute(query, values)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"Inserted row into {table}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving values: {e}")
        return False
