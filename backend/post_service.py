import os
from .database import db
from .utils import save_image, save_video

class PostService:
    @staticmethod
    def create_post(user_id, title, content, image_files, category='推荐', video_file=None):
        """Create a new post with multiple images or a video."""
        # 输入验证
        if not title or len(title.strip()) < 1:
            return False, "标题不能为空"
        if len(title) > 100:
            return False, "标题不能超过100个字符"
        if content and len(content) > 10000:
            return False, "内容不能超过10000个字符"
        if category and len(category) > 50:
            return False, "分类名称过长"
        
        if (not image_files or len(image_files) == 0) and not video_file:
            return False, "必须上传图片或视频"
        
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            # Save all images
            image_urls = []
            if image_files:
                for img in image_files:
                    url = save_image(img)
                    if url:
                        image_urls.append(url)
            
            if not image_urls and not video_file:
                return False, "Failed to save images"

            video_url = None
            if video_file:
                video_url = save_video(video_file)
                if not video_url:
                    return False, "Failed to save video"

            # First image is the cover (required for both image posts and video posts)
            if not image_urls:
                 return False, "必须上传封面图片"

            cover_image = image_urls[0]
            
            with conn.cursor() as cursor:
                # Insert into posts
                sql = "INSERT INTO posts (user_id, title, content, image_url, video_url, category, is_private) VALUES (%s, %s, %s, %s, %s, %s, FALSE)"
                cursor.execute(sql, (user_id, title.strip(), content.strip() if content else None, cover_image, video_url, category))
                post_id = cursor.lastrowid
                
                # Insert into post_images
                if post_id and image_urls:
                    image_values = [(post_id, url, idx) for idx, url in enumerate(image_urls)]
                    cursor.executemany(
                        "INSERT INTO post_images (post_id, image_url, sort_order) VALUES (%s, %s, %s)",
                        image_values
                    )
                
            return True, "Post created successfully"
        except ValueError as e:
            return False, str(e)  # 文件验证错误
        except Exception as e:
            print(f"Create post error: {e}")
            return False, "Failed to create post"

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
                
                # Get all images for this post
                cursor.execute("SELECT image_url FROM post_images WHERE post_id = %s ORDER BY sort_order ASC", (post_id,))
                images = [row['image_url'] for row in cursor.fetchall()]
                
                # If no images in post_images table (legacy posts), use the one from posts table
                if not images and post['image_url']:
                    images = [post['image_url']]
                
                post['images'] = images
                
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

                    # Notification: Send a message to the post owner
                    try:
                        # Get post owner and title
                        post_sql = "SELECT user_id, title FROM posts WHERE id = %s"
                        cursor.execute(post_sql, (post_id,))
                        post = cursor.fetchone()

                        if post and post['user_id'] != user_id:
                            owner_id = post['user_id']
                            title = post['title']
                            content = f"赞了你的帖子《{title}》"
                            
                            # Insert notification
                            content = f"赞了你的帖子《{title}》"
                            notify_sql = """
                                INSERT INTO notifications (receiver_id, sender_id, type, target_id, content) 
                                VALUES (%s, %s, 'like_post', %s, %s)
                            """
                            cursor.execute(notify_sql, (owner_id, user_id, post_id, content))
                    except Exception as e:
                        print(f"Error sending like notification: {e}")
                        # Continue even if notification fails

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
        # 输入验证
        if not content or len(content.strip()) < 1:
            return False, "评论内容不能为空"
        if len(content) > 1000:
            return False, "评论内容不能超过1000个字符"
        
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"

        try:
            with conn.cursor() as cursor:
                # 验证帖子是否存在
                cursor.execute("SELECT id FROM posts WHERE id = %s", (post_id,))
                if not cursor.fetchone():
                    return False, "帖子不存在"
                
                sql = "INSERT INTO comments (user_id, post_id, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (user_id, post_id, content.strip()))
            return True, "评论成功"
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False, "评论失败"

    @staticmethod
    def get_comments(post_id, current_user_id=None):
        """Get comments for a post."""
        conn = db.get_connection()
        if not conn:
            return []

        try:
            with conn.cursor() as cursor:
                if current_user_id:
                    sql = """
                        SELECT c.*, u.nickname, u.avatar_url,
                        CASE WHEN cl.id IS NOT NULL THEN 1 ELSE 0 END as is_liked
                        FROM comments c 
                        JOIN users u ON c.user_id = u.id 
                        LEFT JOIN comment_likes cl ON c.id = cl.comment_id AND cl.user_id = %s
                        WHERE c.post_id = %s 
                        ORDER BY c.created_at ASC
                    """
                    cursor.execute(sql, (current_user_id, post_id))
                else:
                    sql = """
                        SELECT c.*, u.nickname, u.avatar_url, 0 as is_liked
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
    def toggle_comment_like(user_id, comment_id):
        """Toggle like on a comment."""
        conn = db.get_connection()
        if not conn:
            return False, "DB Error"

        try:
            with conn.cursor() as cursor:
                # Check if already liked
                check_sql = "SELECT id FROM comment_likes WHERE user_id = %s AND comment_id = %s"
                cursor.execute(check_sql, (user_id, comment_id))
                existing_like = cursor.fetchone()

                if existing_like:
                    # Unlike
                    delete_sql = "DELETE FROM comment_likes WHERE id = %s"
                    cursor.execute(delete_sql, (existing_like['id'],))
                    update_sql = "UPDATE comments SET likes_count = likes_count - 1 WHERE id = %s"
                    cursor.execute(update_sql, (comment_id,))
                    return True, "Unliked"
                else:
                    # Like
                    insert_sql = "INSERT INTO comment_likes (user_id, comment_id) VALUES (%s, %s)"
                    cursor.execute(insert_sql, (user_id, comment_id))
                    update_sql = "UPDATE comments SET likes_count = likes_count + 1 WHERE id = %s"
                    cursor.execute(update_sql, (comment_id,))
                    return True, "Liked"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_post(post_id, user_id):
        """Delete a post and its associated files."""
        conn = db.get_connection()
        if not conn:
            return False, "Database connection failed"
        
        try:
            with conn.cursor() as cursor:
                # Verify ownership
                cursor.execute("SELECT user_id, image_url, video_url FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return False, "Post not found"
                if post['user_id'] != user_id:
                    return False, "Permission denied"
                
                # Collect all file paths to delete
                files_to_delete = []
                
                # Add cover image if exists
                if post.get('image_url'):
                    files_to_delete.append(post['image_url'])
                
                # Add video if exists
                if post.get('video_url'):
                    files_to_delete.append(post['video_url'])
                
                # Get all images from post_images table
                cursor.execute("SELECT image_url FROM post_images WHERE post_id = %s", (post_id,))
                post_images = cursor.fetchall()
                for img in post_images:
                    if img.get('image_url'):
                        files_to_delete.append(img['image_url'])
                
                # Delete physical files
                for file_path in files_to_delete:
                    try:
                        if file_path and os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Deleted file: {file_path}")
                    except Exception as e:
                        print(f"Warning: Failed to delete file {file_path}: {e}")
                        # Continue even if file deletion fails
                
                # Delete from database (CASCADE will handle related records)
                cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
                conn.commit()
                return True, "Post deleted successfully"
        except Exception as e:
            conn.rollback()
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
