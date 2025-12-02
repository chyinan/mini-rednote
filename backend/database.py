import os
import pymysql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.connection = None
        return cls._instance

    def connect(self):
        """Establish a database connection."""
        try:
            if self.connection and self.connection.open:
                return self.connection
            
            self.connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'mini_redbook'),
                port=int(os.getenv('DB_PORT', 3306)),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            return self.connection
        except pymysql.MySQLError as e:
            print(f"Error connecting to database: {e}")
            return None

    def get_connection(self):
        """Get the current connection, reconnecting if necessary."""
        return self.connect()

    def close(self):
        """Close the database connection."""
        if self.connection and self.connection.open:
            self.connection.close()

# Global DB instance
db = Database()










