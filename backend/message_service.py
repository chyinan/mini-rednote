from .database import db
from typing import List, Dict, Any

class MessageService:
    @staticmethod
    def send_message(sender_id: int, receiver_id: int, content: str):
        """Send a message from one user to another."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn.cursor() as cursor:
                # Check if receiver exists
                check_sql = "SELECT id FROM users WHERE id = %s"
                cursor.execute(check_sql, (receiver_id,))
                if not cursor.fetchone():
                    return False, "Receiver not found"

                sql = """
                    INSERT INTO messages (sender_id, receiver_id, content) 
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql, (sender_id, receiver_id, content))
            return True, "Message sent successfully"
        except Exception as e:
            return False, f"Failed to send message: {str(e)}"

    @staticmethod
    def get_conversation(user1_id: int, user2_id: int, limit: int = 50, offset: int = 0):
        """Get messages between two users."""
        conn = db.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT m.*, 
                           s.nickname as sender_name, s.avatar_url as sender_avatar,
                           r.nickname as receiver_name, r.avatar_url as receiver_avatar
                    FROM messages m
                    JOIN users s ON m.sender_id = s.id
                    JOIN users r ON m.receiver_id = r.id
                    WHERE (m.sender_id = %s AND m.receiver_id = %s) 
                       OR (m.sender_id = %s AND m.receiver_id = %s)
                    ORDER BY m.created_at DESC
                    LIMIT %s OFFSET %s
                """
                cursor.execute(sql, (user1_id, user2_id, user2_id, user1_id, limit, offset))
                messages = cursor.fetchall()
                return messages[::-1] # Return in chronological order
        except Exception as e:
            print(f"Error fetching conversation: {e}")
            return []

    @staticmethod
    def get_conversations(user_id: int):
        """Get list of recent conversations for a user."""
        conn = db.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                # This query is a bit complex. It gets the latest message for each unique conversation partner.
                # We need to group by the "other" user.
                sql = """
                    SELECT 
                        CASE 
                            WHEN sender_id = %s THEN receiver_id 
                            ELSE sender_id 
                        END as other_user_id,
                        MAX(created_at) as last_msg_time
                    FROM messages
                    WHERE sender_id = %s OR receiver_id = %s
                    GROUP BY other_user_id
                    ORDER BY last_msg_time DESC
                """
                cursor.execute(sql, (user_id, user_id, user_id))
                conversations = cursor.fetchall()
                
                # Now fetch details for each conversation
                results = []
                for conv in conversations:
                    other_id = conv['other_user_id']
                    
                    # Get user info
                    user_sql = "SELECT id, nickname, avatar_url FROM users WHERE id = %s"
                    cursor.execute(user_sql, (other_id,))
                    other_user = cursor.fetchone()
                    
                    # Get last message content and unread count
                    msg_sql = """
                        SELECT content, is_read, sender_id 
                        FROM messages 
                        WHERE (sender_id = %s AND receiver_id = %s) 
                           OR (sender_id = %s AND receiver_id = %s)
                        ORDER BY created_at DESC LIMIT 1
                    """
                    cursor.execute(msg_sql, (user_id, other_id, other_id, user_id))
                    last_msg = cursor.fetchone()
                    
                    unread_sql = """
                        SELECT COUNT(*) as count 
                        FROM messages 
                        WHERE sender_id = %s AND receiver_id = %s AND is_read = FALSE
                    """
                    cursor.execute(unread_sql, (other_id, user_id))
                    unread = cursor.fetchone()
                    
                    if other_user and last_msg:
                        results.append({
                            "user": other_user,
                            "last_message": last_msg,
                            "unread_count": unread['count'],
                            "timestamp": conv['last_msg_time']
                        })
                return results
        except Exception as e:
            print(f"Error fetching conversations: {e}")
            return []

    @staticmethod
    def mark_messages_read(user_id: int, sender_id: int):
        """Mark all messages from sender_id to user_id as read."""
        conn = db.get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE messages 
                    SET is_read = TRUE 
                    WHERE sender_id = %s AND receiver_id = %s AND is_read = FALSE
                """
                cursor.execute(sql, (sender_id, user_id))
            return True
        except Exception as e:
            print(f"Error marking messages read: {e}")
            return False

    @staticmethod
    def get_total_unread_count(user_id: int):
        """Get total count of unread messages and notifications for a user."""
        conn = db.get_connection()
        if not conn:
            return 0

        try:
            with conn.cursor() as cursor:
                # Count unread messages
                msg_sql = "SELECT COUNT(*) as count FROM messages WHERE receiver_id = %s AND is_read = FALSE"
                cursor.execute(msg_sql, (user_id,))
                msg_result = cursor.fetchone()
                msg_count = msg_result['count'] if msg_result else 0

                # Count unread notifications
                notify_sql = "SELECT COUNT(*) as count FROM notifications WHERE receiver_id = %s AND is_read = FALSE"
                cursor.execute(notify_sql, (user_id,))
                notify_result = cursor.fetchone()
                notify_count = notify_result['count'] if notify_result else 0

                return msg_count + notify_count
        except Exception as e:
            print(f"Error getting unread count: {e}")
            return 0

    @staticmethod
    def get_notifications(user_id: int):
        """Get notifications for a user."""
        conn = db.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT n.*, 
                           u.nickname as sender_name, u.avatar_url as sender_avatar,
                           p.title as post_title, p.image_url as post_image
                    FROM notifications n
                    JOIN users u ON n.sender_id = u.id
                    LEFT JOIN posts p ON n.target_id = p.id
                    WHERE n.receiver_id = %s
                    ORDER BY n.created_at DESC
                """
                cursor.execute(sql, (user_id,))
                notifications = cursor.fetchall()
                return notifications
        except Exception as e:
            print(f"Error fetching notifications: {e}")
            return []

    @staticmethod
    def mark_notifications_read(user_id: int):
        """Mark all notifications as read."""
        conn = db.get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                sql = "UPDATE notifications SET is_read = TRUE WHERE receiver_id = %s"
                cursor.execute(sql, (user_id,))
            return True
        except Exception as e:
            print(f"Error marking notifications read: {e}")
            return False




