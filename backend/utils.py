import os
import uuid
from PIL import Image

IMAGE_DIR = "assets"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB (Increased from 10MB)
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}

def validate_image_file(uploaded_file):
    """Validate uploaded image file."""
    # 检查文件名
    if not uploaded_file.filename:
        return False, "文件名不能为空"
    
    # 检查文件扩展名
    file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"不支持的文件类型，仅支持: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # 检查文件大小
    file_content = uploaded_file.file.read()
    uploaded_file.file.seek(0)  # 重置文件指针
    
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"图片大小不能超过 {MAX_FILE_SIZE // (1024*1024)}MB"
    
    if len(file_content) == 0:
        return False, "文件不能为空"
    
    # 验证文件内容（检查是否为真实图片）
    try:
        # 使用PIL验证图片
        img = Image.open(uploaded_file.file)
        img.verify()
        
        # 使用 format 进行格式检查
        image_type = img.format.lower() if img.format else None
        
        uploaded_file.file.seek(0)  # 重置文件指针
        
        # 检查MIME类型
        if hasattr(uploaded_file, 'content_type') and uploaded_file.content_type:
            if uploaded_file.content_type not in ALLOWED_MIME_TYPES:
                return False, "文件类型不匹配"
        
        if not image_type:
            return False, "无法识别图片格式"
        
        # 验证扩展名与内容匹配
        ext_to_type = {
            '.jpg': 'jpeg', '.jpeg': 'jpeg',
            '.png': 'png',
            '.gif': 'gif',
            '.webp': 'webp'
        }
        expected_type = ext_to_type.get(file_ext)
        if expected_type and image_type != expected_type:
            return False, "文件扩展名与内容不匹配"
            
    except Exception as e:
        return False, f"无效的图片文件: {str(e)}"
    
    return True, "验证通过"

def validate_video_file(uploaded_file):
    """Validate uploaded video file."""
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.webm'}
    MAX_VIDEO_SIZE = 10 * 1024 * 1024 * 1024  # 10GB

    if not uploaded_file.filename:
        return False, "文件名不能为空"
    
    file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
    if file_ext not in ALLOWED_VIDEO_EXTENSIONS:
        return False, f"不支持的视频类型，仅支持: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
    
    # Check file size
    uploaded_file.file.seek(0, 2) # Seek to end
    size = uploaded_file.file.tell()
    uploaded_file.file.seek(0) # Reset

    if size > MAX_VIDEO_SIZE:
        return False, f"视频大小不能超过 {MAX_VIDEO_SIZE // (1024*1024*1024)}GB"
    
    if size == 0:
        return False, "文件不能为空"

    return True, "验证通过"

def save_video(uploaded_file):
    """Save uploaded video to assets directory."""
    is_valid, message = validate_video_file(uploaded_file)
    if not is_valid:
        raise ValueError(message)

    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(IMAGE_DIR, unique_filename)

    uploaded_file.file.seek(0)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.file.read())
    
    return file_path

def save_image(uploaded_file):
    """Save uploaded image to assets directory and return the path."""
    # 验证文件
    is_valid, message = validate_image_file(uploaded_file)
    if not is_valid:
        raise ValueError(message)
    
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
    
    # 使用安全的文件名（只保留扩展名）
    file_ext = os.path.splitext(uploaded_file.filename)[1].lower()
    # 确保扩展名在允许列表中
    if file_ext not in ALLOWED_EXTENSIONS:
        file_ext = '.jpg'  # 默认扩展名
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(IMAGE_DIR, unique_filename)
    
    # 重新打开并保存图片（确保是有效图片）
    try:
        img = Image.open(uploaded_file.file)
        # 转换为RGB模式（处理RGBA等）
        if img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 保存图片
        img.save(file_path, 'JPEG', quality=85, optimize=True)
        return file_path
    except Exception as e:
        # 如果处理失败，尝试直接保存
        uploaded_file.file.seek(0)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.file.read())
        return file_path

