from fastapi.testclient import TestClient
from server import app
import pytest
from backend.auth_service import AuthService
from io import BytesIO
from PIL import Image

client = TestClient(app)

def create_test_image():
    """Create a test image file for testing."""
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return ('test.jpg', img_bytes, 'image/jpeg')

def test_api_register_success(mock_db, mocker):
    mock_conn, mock_cursor = mock_db
    # First query checks for existing user -> returns None
    mock_cursor.fetchone.return_value = None
    
    # Mock save_image to return a fake path
    mocker.patch('backend.auth_service.save_image', return_value='assets/test-avatar.jpg')
    
    filename, file_content, content_type = create_test_image()
    
    response = client.post("/api/register", 
        data={
            "username": "apiuser",
            "password": "password123"
        },
        files={"avatar": (filename, file_content, content_type)}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Verify DB interaction
    # Expect check select and insert
    assert mock_cursor.execute.call_count >= 1

def test_api_register_missing_avatar():
    """Test that registration fails without avatar."""
    response = client.post("/api/register", data={
        "username": "apiuser",
        "password": "password123"
    })
    
    # Should return 422 (Unprocessable Entity) because avatar is required
    assert response.status_code == 422

def test_api_login_success(mock_db):
    mock_conn, mock_cursor = mock_db
    
    # Prepare mocked user in DB
    hashed = AuthService.hash_password("secret")
    user_data = {
        "id": 10,
        "username": "loginuser",
        "nickname": "Login User",
        "avatar_url": None,
        "password_hash": hashed
    }
    mock_cursor.fetchone.return_value = user_data
    
    response = client.post("/api/login", json={
        "username": "loginuser",
        "password": "secret"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["id"] == 10

def test_get_posts_mocked_service(mocker):
    # Mock the PostService.get_posts method to test API layer without DB
    mock_posts = {
        "posts": [
            {"id": 1, "title": "Test Post", "content": "Content"}
        ],
        "has_more": False
    }
    mocker.patch("backend.post_service.PostService.get_posts", return_value=mock_posts)
    
    response = client.get("/api/posts")
    
    assert response.status_code == 200
    assert response.json() == mock_posts

def test_create_post_validation_error():
    # Test validation without mocking DB (fails before DB access)
    response = client.post("/api/posts", data={
        "user_id": 1,
        "title": "Title",
        "content": "Content",
        "category": "Daily"
    })
    # Expect 400 because images or video is required
    assert response.status_code == 400
    assert "Images or Video required" in response.json()["detail"]

