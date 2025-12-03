import pytest
from backend.auth_service import AuthService
from unittest.mock import Mock
from io import BytesIO
from PIL import Image

def create_mock_avatar_file():
    """Create a mock avatar file for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    mock_file = Mock()
    mock_file.filename = 'test.jpg'
    mock_file.file = img_bytes
    mock_file.content_type = 'image/jpeg'
    return mock_file

def test_register_user_success(mock_db, mocker):
    mock_conn, mock_cursor = mock_db
    
    # Setup mock for check_sql (user does not exist) -> fetchone returns None
    mock_cursor.fetchone.return_value = None
    
    # Mock save_image to return a fake path
    mocker.patch('backend.auth_service.save_image', return_value='assets/test-avatar.jpg')
    
    mock_avatar = create_mock_avatar_file()
    success, msg = AuthService.register_user("testuser", "password123", avatar_file=mock_avatar)
    
    assert success is True
    assert msg == "Registration successful"
    
    # Verify SQL executions
    # We expect check SQL then Insert SQL
    assert mock_cursor.execute.call_count == 2
    args, _ = mock_cursor.execute.call_args  # Get args of last call
    assert "INSERT INTO users" in args[0]

def test_register_user_missing_avatar():
    """Test that registration fails without avatar."""
    success, msg = AuthService.register_user("testuser", "password123")
    
    assert success is False
    assert "请上传头像" in msg
    
def test_register_user_already_exists(mock_db, mocker):
    mock_conn, mock_cursor = mock_db
    
    # Setup mock (user exists)
    mock_cursor.fetchone.return_value = {"id": 1}
    
    # Mock save_image to return a fake path
    mocker.patch('backend.auth_service.save_image', return_value='assets/test-avatar.jpg')
    
    mock_avatar = create_mock_avatar_file()
    success, msg = AuthService.register_user("existinguser", "password123", avatar_file=mock_avatar)
    
    assert success is False
    assert "用户名已存在" in msg

def test_login_user_success(mock_db):
    mock_conn, mock_cursor = mock_db
    
    # Mock user data in DB
    # We need a real hash for the verify_password to work, 
    # because AuthService.login_user calls verify_password which uses bcrypt
    hashed = AuthService.hash_password("password123")
    user_data = {
        "id": 1,
        "username": "testuser", 
        "nickname": "Test", 
        "avatar_url": None,
        "password_hash": hashed
    }
    mock_cursor.fetchone.return_value = user_data
    
    user, msg = AuthService.login_user("testuser", "password123")
    
    assert user is not None
    assert user["username"] == "testuser"
    assert msg == "Login successful"
    # Ensure password hash is removed from returned user object
    assert "password_hash" not in user

def test_login_user_wrong_password(mock_db):
    mock_conn, mock_cursor = mock_db
    
    hashed = AuthService.hash_password("password123")
    user_data = {
        "id": 1,
        "username": "testuser", 
        "password_hash": hashed
    }
    mock_cursor.fetchone.return_value = user_data
    
    user, msg = AuthService.login_user("testuser", "wrongpass")
    
    assert user is None
    assert msg == "用户名或密码错误"

def test_login_user_not_found(mock_db):
    mock_conn, mock_cursor = mock_db
    
    mock_cursor.fetchone.return_value = None
    
    user, msg = AuthService.login_user("nonexistent", "password123")
    
    assert user is None
    assert msg == "用户名或密码错误"

