import pytest
from unittest.mock import MagicMock
from backend.post_service import PostService

def test_create_post_validation_empty_title():
    result, msg = PostService.create_post(1, "", "content", [])
    assert result is False
    assert "标题不能为空" in msg

def test_create_post_validation_no_media():
    result, msg = PostService.create_post(1, "Title", "content", [])
    assert result is False
    assert "必须上传图片或视频" in msg

def test_create_post_success(mock_db, mocker):
    mock_conn, mock_cursor = mock_db
    
    # Mock save_image to return a fake path
    mocker.patch('backend.post_service.save_image', return_value="assets/test.jpg")
    
    # Mock files (list of dummy objects)
    files = [MagicMock()]
    
    mock_cursor.lastrowid = 100
    
    success, msg = PostService.create_post(1, "Title", "Content", files)
    
    assert success is True
    assert msg == "Post created successfully"
    
    # Verify DB insertion
    # We expect Insert Post, then possibly Insert Images
    calls = mock_cursor.execute.call_args_list
    assert len(calls) >= 1
    
    # Check that at least one call was INSERT INTO posts
    insert_post_called = any("INSERT INTO posts" in str(call) for call in calls)
    assert insert_post_called

def test_toggle_like_new(mock_db):
    mock_conn, mock_cursor = mock_db
    
    # Mock check: not liked yet
    mock_cursor.fetchone.return_value = None
    
    # Mock post fetch for notification
    # We need to configure side_effect for fetchone because it's called multiple times
    # 1. check_sql (None)
    # 2. post_sql (Returns post dict)
    mock_cursor.fetchone.side_effect = [None, {"user_id": 2, "title": "Test Post"}]
    
    success, msg = PostService.toggle_like(1, 100)
    
    assert success is True
    assert msg == "Liked"
    
    # Verify INSERT like and UPDATE post count
    # Also INSERT notification
    assert mock_cursor.execute.call_count >= 3






