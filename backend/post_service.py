import os
from .database import db
from .utils import save_image

class PostService:
    @staticmethod
    def create_post(user_id, title, content, image_file, category='推荐'):
        """Create a new post."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            image_url = save_image(image_file) if image_file else None
            
            with conn.cursor() as cursor:
                sql = "INSERT INTO posts (user_id, title, content, image_url, category, is_private) VALUES (%s, %s, %s, %s, %s, FALSE)"
                cursor.execute(sql, (user_id, title, content, image_url, category))
            return True, "Post created successfully"
        except Exception as e:
            return False, f"Failed to create post: {str(e)}"

    @staticmethod
    def get_posts(limit=20, offset=0, search_query=None, category=None):
        """Fetch posts with optional search and category filter."""
        conn = db.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                # Only show public posts in feed
                sql_parts = ["""
                    SELECT p.*, u.nickname, u.avatar_url 
                    FROM posts p 
                    JOIN users u ON p.user_id = u.id 
                    WHERE p.is_private = FALSE
                """]
                params = []
                
                if search_query:
                    # Simple search logic
                    sql_parts.append("AND (p.title LIKE %s OR p.content LIKE %s)")
                    like_query = f"%{search_query}%"
                    params.extend([like_query, like_query])
                
                if category and category != '推荐':
                    sql_parts.append("AND p.category = %s")
                    params.append(category)

                # Randomize for 'Recommend' feed to ensure visibility for all posts
                if (not category or category == '推荐') and not search_query:
                    sql_parts.append("ORDER BY RAND() LIMIT %s OFFSET %s")
                else:
                    sql_parts.append("ORDER BY p.created_at DESC LIMIT %s OFFSET %s")
                    
                params.extend([limit, offset])

                sql = " ".join(sql_parts)
                cursor.execute(sql, tuple(params))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching posts: {e}")
            return []

    @staticmethod
    def get_post_by_id(post_id, current_user_id=None):
        """Get a single post details, optionally with user interaction status."""
        conn = db.get_connection()
        if not conn:
            print("Database connection failed")
            return None

        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT p.*, u.nickname, u.avatar_url 
                    FROM posts p 
                    JOIN users u ON p.user_id = u.id 
                    WHERE p.id = %s
                """
                cursor.execute(sql, (post_id,))
                post = cursor.fetchone()
                
                # If post not found, return None
                if not post:
                    print(f"Post with id {post_id} not found")
                    return None
                
                # Check privacy
                if post['is_private'] and (not current_user_id or post['user_id'] != current_user_id):
                    # If private and not owner, treat as not found or unauthorized
                    # For now, return None to hide it
                    print(f"Post {post_id} is private")
                    return None
                
                # Initialize interaction status
                post['is_liked'] = False
                post['is_collected'] = False
                
                # Check interaction status if user is logged in
                if current_user_id:
                    # Check if liked
                    cursor.execute(
                        "SELECT id FROM likes WHERE user_id = %s AND post_id = %s", 
                        (current_user_id, post_id)
                    )
                    post['is_liked'] = bool(cursor.fetchone())
                    
                    # Check if collected
                    cursor.execute(
                        "SELECT id FROM collections WHERE user_id = %s AND post_id = %s", 
                        (current_user_id, post_id)
                    )
                    post['is_collected'] = bool(cursor.fetchone())
                    
                return post
        except Exception as e:
            print(f"Error fetching post: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def get_user_posts(target_user_id, current_user_id=None):
        """Get posts by a specific user."""
        conn = db.get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT p.*, u.nickname, u.avatar_url 
                    FROM posts p
                    JOIN users u ON p.user_id = u.id
                    WHERE p.user_id = %s 
                """
                params = [target_user_id]
                
                # If not owner, only show public posts
                if str(target_user_id) != str(current_user_id):
                    sql += " AND p.is_private = FALSE"
                
                sql += " ORDER BY p.created_at DESC"
                
                cursor.execute(sql, tuple(params))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching user posts: {e}")
            return []

    @staticmethod
    def get_user_liked_posts(user_id):
        """Get posts liked by a specific user."""
        conn = db.get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cursor:
                # Need to join with users table to get author info
                # Only show public posts in likes list? Or show all since user liked them?
                # Usually, if I like a private post (which shouldn't happen unless I'm owner), it's fine.
                # But if post becomes private, should it disappear from my likes?
                # For simplicity, filter out private posts unless I am the owner of the POST (not liker).
                # But simpler: just filter is_private=FALSE for now.
                sql = """
                    SELECT p.*, u.nickname, u.avatar_url 
                    FROM posts p
                    JOIN likes l ON p.id = l.post_id
                    JOIN users u ON p.user_id = u.id
                    WHERE l.user_id = %s AND p.is_private = FALSE
                    ORDER BY l.created_at DESC
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching liked posts: {e}")
            return []

    @staticmethod
    def get_user_collected_posts(user_id):
        """Get posts collected by a specific user."""
        conn = db.get_connection()
        if not conn:
            return []
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT p.*, u.nickname, u.avatar_url 
                    FROM posts p
                    JOIN collections c ON p.id = c.post_id
                    JOIN users u ON p.user_id = u.id
                    WHERE c.user_id = %s AND p.is_private = FALSE
                    ORDER BY c.created_at DESC
                """
                cursor.execute(sql, (user_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching collected posts: {e}")
            return []

    @staticmethod
    def toggle_like(user_id, post_id):
        """Toggle like on a post."""
        conn = db.get_connection()
        if not conn:
            return False, "DB Error"

        try:
            with conn.cursor() as cursor:
                # Check if already liked
                check_sql = "SELECT id FROM likes WHERE user_id = %s AND post_id = %s"
                cursor.execute(check_sql, (user_id, post_id))
                existing_like = cursor.fetchone()

                if existing_like:
                    # Unlike
                    delete_sql = "DELETE FROM likes WHERE id = %s"
                    cursor.execute(delete_sql, (existing_like['id'],))
                    update_sql = "UPDATE posts SET likes_count = likes_count - 1 WHERE id = %s"
                    cursor.execute(update_sql, (post_id,))
                    return True, "Unliked"
                else:
                    # Like
                    insert_sql = "INSERT INTO likes (user_id, post_id) VALUES (%s, %s)"
                    cursor.execute(insert_sql, (user_id, post_id))
                    update_sql = "UPDATE posts SET likes_count = likes_count + 1 WHERE id = %s"
                    cursor.execute(update_sql, (post_id,))
                    return True, "Liked"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def toggle_collection(user_id, post_id):
        """Toggle collection on a post."""
        conn = db.get_connection()
        if not conn:
            return False, "DB Error"

        try:
            with conn.cursor() as cursor:
                # Check if already collected
                check_sql = "SELECT id FROM collections WHERE user_id = %s AND post_id = %s"
                cursor.execute(check_sql, (user_id, post_id))
                existing_collection = cursor.fetchone()

                if existing_collection:
                    # Uncollect
                    delete_sql = "DELETE FROM collections WHERE id = %s"
                    cursor.execute(delete_sql, (existing_collection['id'],))
                    return True, "Uncollected"
                else:
                    # Collect
                    insert_sql = "INSERT INTO collections (user_id, post_id) VALUES (%s, %s)"
                    cursor.execute(insert_sql, (user_id, post_id))
                    return True, "Collected"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def add_comment(user_id, post_id, content):
        """Add a comment to a post."""
        conn = db.get_connection()
        if not conn:
            return False

        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO comments (user_id, post_id, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, post_id, content))
            return True
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False

    @staticmethod
    def get_comments(post_id):
        """Get comments for a post."""
        conn = db.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT c.*, u.nickname, u.avatar_url 
                    FROM comments c 
                    JOIN users u ON c.user_id = u.id 
                    WHERE c.post_id = %s 
                    ORDER BY c.created_at ASC
                """
                cursor.execute(sql, (post_id,))
                return cursor.fetchall()
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []

    @staticmethod
    def delete_post(post_id, user_id):
        """Delete a post."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            with conn.cursor() as cursor:
                # Verify ownership
                cursor.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return False, "Post not found"
                if post['user_id'] != user_id:
                    return False, "Permission denied"
                
                cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
                return True, "Post deleted successfully"
        except Exception as e:
            return False, f"Failed to delete post: {str(e)}"

    @staticmethod
    def update_post_visibility(post_id, user_id, is_private):
        """Update post visibility."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"
            
        try:
            with conn.cursor() as cursor:
                # Verify ownership
                cursor.execute("SELECT user_id FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return False, "Post not found"
                if post['user_id'] != user_id:
                    return False, "Permission denied"
                
                cursor.execute("UPDATE posts SET is_private = %s WHERE id = %s", (is_private, post_id))
                return True, "Visibility updated successfully"
        except Exception as e:
            return False, f"Failed to update visibility: {str(e)}"
