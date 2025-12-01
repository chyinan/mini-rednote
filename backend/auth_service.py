import hashlib
import datetime
from .database import db
from .utils import save_image

class AuthService:
    @staticmethod
    def hash_password(password):
        """Hash a password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def register_user(username, password, nickname=None):
        """Register a new user."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        password_hash = AuthService.hash_password(password)
        nickname = nickname or username
        
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO users (username, password_hash, nickname) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, password_hash, nickname))
            return True, "Registration successful"
        except Exception as e:
            return False, f"Registration failed: {str(e)}"

    @staticmethod
    def login_user(username, password):
        """Authenticate a user."""
        conn = db.get_connection()
        if not conn:
            return None, "Database connection failed"

        password_hash = AuthService.hash_password(password)
        
        try:
            with conn.cursor() as cursor:
                sql = "SELECT id, username, nickname, avatar_url FROM users WHERE username = %s AND password_hash = %s"
                cursor.execute(sql, (username, password_hash))
                user = cursor.fetchone()
                if user:
                    return user, "Login successful"
                return None, "Invalid username or password"
        except Exception as e:
            return None, f"Login failed: {str(e)}"

    @staticmethod
    def get_user_by_id(user_id):
        """Get user info by ID."""
        conn = db.get_connection()
        if not conn:
            return None

        try:
            with conn.cursor() as cursor:
                sql = "SELECT id, username, nickname, avatar_url FROM users WHERE id = %s"
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    @staticmethod
    def update_user_profile(user_id, nickname, avatar_file=None):
        """Update user profile."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            avatar_url = None
            if avatar_file:
                avatar_url = save_image(avatar_file)

            with conn.cursor() as cursor:
                if avatar_url:
                    sql = "UPDATE users SET nickname = %s, avatar_url = %s WHERE id = %s"
                    cursor.execute(sql, (nickname, avatar_url, user_id))
                else:
                    sql = "UPDATE users SET nickname = %s WHERE id = %s"
                    cursor.execute(sql, (nickname, user_id))
            return True, "Profile updated successfully"
        except Exception as e:
            return False, f"Update failed: {str(e)}"
