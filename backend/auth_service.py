import bcrypt
from .database import db
from .utils import save_image

class AuthService:
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        """Verify a password against a hash."""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def register_user(username, password, nickname=None, avatar_file=None):
        """Register a new user."""
        # 输入验证
        if not username or len(username.strip()) < 3:
            return False, "用户名至少需要3个字符"
        if len(username) > 50:
            return False, "用户名不能超过50个字符"
        if not password or len(password) < 6:
            return False, "密码至少需要6个字符"
        if len(password) > 128:
            return False, "密码不能超过128个字符"
        if nickname and len(nickname) > 50:
            return False, "昵称不能超过50个字符"
        
        # 头像为必填项
        if not avatar_file:
            return False, "请上传头像"
        
        # 清理输入
        username = username.strip()
        if nickname:
            nickname = nickname.strip()
        
        # 处理头像
        avatar_url = None
        try:
            avatar_url = save_image(avatar_file)
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, "头像上传失败"

        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        password_hash = AuthService.hash_password(password)
        nickname = nickname or username
        
        try:
            with conn.cursor() as cursor:
                # 检查用户名是否已存在
                check_sql = "SELECT id FROM users WHERE username = %s"
                cursor.execute(check_sql, (username,))
                if cursor.fetchone():
                    return False, "用户名已存在，请选择其他用户名"
                
                # 用户名不存在，执行插入
                sql = "INSERT INTO users (username, password_hash, nickname, avatar_url) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (username, password_hash, nickname, avatar_url))
            return True, "Registration successful"
        except Exception as e:
            return False, "Registration failed"

    @staticmethod
    def login_user(username, password):
        """Authenticate a user."""
        conn = db.get_connection()
        if not conn:
            return None, "Database connection failed"
        
        try:
            with conn.cursor() as cursor:
                # 先获取用户信息（包括密码哈希）
                sql = "SELECT id, username, nickname, avatar_url, password_hash FROM users WHERE username = %s"
                cursor.execute(sql, (username,))
                user = cursor.fetchone()
                
                if user and AuthService.verify_password(password, user['password_hash']):
                    # 移除密码哈希，不返回给客户端
                    del user['password_hash']
                    return user, "Login successful"
                return None, "用户名或密码错误"
        except Exception as e:
            return None, "登录失败"

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
        # 输入验证
        if not nickname or len(nickname.strip()) < 1:
            return False, "昵称不能为空"
        if len(nickname) > 50:
            return False, "昵称不能超过50个字符"
        
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            avatar_url = None
            if avatar_file:
                avatar_url = save_image(avatar_file)

            with conn.cursor() as cursor:
                # 验证用户是否存在
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    return False, "用户不存在"
                
                if avatar_url:
                    sql = "UPDATE users SET nickname = %s, avatar_url = %s WHERE id = %s"
                    cursor.execute(sql, (nickname.strip(), avatar_url, user_id))
                else:
                    sql = "UPDATE users SET nickname = %s WHERE id = %s"
                    cursor.execute(sql, (nickname.strip(), user_id))
            return True, "Profile updated successfully"
        except ValueError as e:
            return False, str(e)  # 文件验证错误
        except Exception as e:
            return False, "Update failed"
