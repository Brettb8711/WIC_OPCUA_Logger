import psycopg2

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

    def insert_data(self, node_id, value, server_url=None):
        if not self.conn:
            raise Exception('Not connected')
        with self.conn.cursor() as cur:
            if server_url:
                cur.execute('''CREATE TABLE IF NOT EXISTS opcua_data (node_id TEXT, value TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, server_url TEXT)''')
                cur.execute('''INSERT INTO opcua_data (node_id, value, server_url) VALUES (%s, %s, %s)''', (node_id, str(value), server_url))
            else:
                cur.execute('''CREATE TABLE IF NOT EXISTS opcua_data (node_id TEXT, value TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
                cur.execute('''INSERT INTO opcua_data (node_id, value) VALUES (%s, %s)''', (node_id, str(value)))
            self.conn.commit()
