from .database import db

class UserService:
    @staticmethod
    def follow_user(follower_id, followed_id):
        """Follow a user."""
        if follower_id == followed_id:
            return False, "Cannot follow yourself"
            
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"
            
        try:
            with conn.cursor() as cursor:
                # Check if already following
                sql_check = "SELECT id FROM follows WHERE follower_id = %s AND followed_id = %s"
                cursor.execute(sql_check, (follower_id, followed_id))
                if cursor.fetchone():
                    return False, "Already following"
                
                sql = "INSERT INTO follows (follower_id, followed_id) VALUES (%s, %s)"
                cursor.execute(sql, (follower_id, followed_id))
                return True, "Followed successfully"
        except Exception as e:
            return False, f"Failed to follow: {str(e)}"

    @staticmethod
    def unfollow_user(follower_id, followed_id):
        """Unfollow a user."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"
            
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM follows WHERE follower_id = %s AND followed_id = %s"
                cursor.execute(sql, (follower_id, followed_id))
                return True, "Unfollowed successfully"
        except Exception as e:
            return False, f"Failed to unfollow: {str(e)}"

    @staticmethod
    def is_following(follower_id, followed_id):
        """Check if a user is following another user."""
        conn = db.get_connection()
        if not conn:
            return False
            
        try:
            with conn.cursor() as cursor:
                sql = "SELECT id FROM follows WHERE follower_id = %s AND followed_id = %s"
                cursor.execute(sql, (follower_id, followed_id))
                return bool(cursor.fetchone())
        except Exception as e:
            print(f"Error checking follow status: {e}")
            return False

    @staticmethod
    def get_followers(user_id, current_user_id=None):
        """Get list of followers for a user."""
        conn = db.get_connection()
        if not conn:
            return []
            
        try:
            with conn.cursor() as cursor:
                if current_user_id:
                    sql = """
                        SELECT u.id, u.username, u.nickname, u.avatar_url,
                        CASE WHEN f2.id IS NOT NULL THEN 1 ELSE 0 END as is_following
                        FROM follows f
                        JOIN users u ON f.follower_id = u.id
                        LEFT JOIN follows f2 ON f2.follower_id = %s AND f2.followed_id = u.id
                        WHERE f.followed_id = %s
                        ORDER BY f.created_at DESC
                    """
                    cursor.execute(sql, (current_user_id, user_id))
                else:
                    sql = """
                        SELECT u.id, u.username, u.nickname, u.avatar_url,
                        0 as is_following
                        FROM follows f
                        JOIN users u ON f.follower_id = u.id
                        WHERE f.followed_id = %s
                        ORDER BY f.created_at DESC
                    """
                    cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching followers: {e}")
            return []

    @staticmethod
    def get_following(user_id, current_user_id=None):
        """Get list of users a user is following."""
        conn = db.get_connection()
        if not conn:
            return []
            
        try:
            with conn.cursor() as cursor:
                if current_user_id:
                    sql = """
                        SELECT u.id, u.username, u.nickname, u.avatar_url,
                        CASE WHEN f2.id IS NOT NULL THEN 1 ELSE 0 END as is_following
                        FROM follows f
                        JOIN users u ON f.followed_id = u.id
                        LEFT JOIN follows f2 ON f2.follower_id = %s AND f2.followed_id = u.id
                        WHERE f.follower_id = %s
                        ORDER BY f.created_at DESC
                    """
                    cursor.execute(sql, (current_user_id, user_id))
                else:
                    sql = """
                        SELECT u.id, u.username, u.nickname, u.avatar_url,
                        0 as is_following
                        FROM follows f
                        JOIN users u ON f.followed_id = u.id
                        WHERE f.follower_id = %s
                        ORDER BY f.created_at DESC
                    """
                    cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching following: {e}")
            return []
    
    @staticmethod
    def get_follow_counts(user_id):
        """Get follower and following counts."""
        conn = db.get_connection()
        if not conn:
            return {'followers': 0, 'following': 0}
            
        try:
            with conn.cursor() as cursor:
                # Count followers
                cursor.execute("SELECT COUNT(*) as count FROM follows WHERE followed_id = %s", (user_id,))
                followers = cursor.fetchone()['count']
                
                # Count following
                cursor.execute("SELECT COUNT(*) as count FROM follows WHERE follower_id = %s", (user_id,))
                following = cursor.fetchone()['count']
                
                return {'followers': followers, 'following': following}
        except Exception as e:
            print(f"Error counting follows: {e}")
            return {'followers': 0, 'following': 0}

