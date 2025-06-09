import psycopg2

# This file was moved to services/postgres_service.py for better project structure.

class PostgresService:
    def __init__(self, conn_str):
        self.conn_str = conn_str
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(self.conn_str)
        return self.conn

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def test_connection(self):
        conn = psycopg2.connect(self.conn_str)
        conn.close()
        return True

    def insert_data(self, node_id, value, server_name=None):
        if not self.conn:
            raise Exception('Not connected')
        with self.conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS opcua_data (
                    node_id TEXT,
                    double_value DOUBLE PRECISION,
                    float_value REAL,
                    int_value INTEGER,
                    bool_value BOOLEAN,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    string_val TEXT,
                    dictionary_val TEXT,
                    server_name TEXT
                )
            ''')

            # Prepare value types
            double_value = float(value) if isinstance(value, float) else None
            float_value = float(value) if isinstance(value, float) else None
            int_value = int(value) if isinstance(value, int) else None
            bool_value = bool(value) if isinstance(value, bool) else None
            string_val = str(value) if isinstance(value, str) else None
            dictionary_val = None

            # If value is a dict, store as JSON string
            import json
            if isinstance(value, dict):
                dictionary_val = json.dumps(value)
                string_val = None  # Don't store dict as string

            cur.execute('''
                INSERT INTO opcua_data (
                    node_id, double_value, float_value, int_value, bool_value, string_val, dictionary_val, server_name
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ''', (node_id, double_value, float_value, int_value, bool_value, string_val, dictionary_val, server_name))
            self.conn.commit()
