import pytest
from unittest.mock import MagicMock
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import db

@pytest.fixture
def mock_db(mocker):
    """
    Mock the database connection and cursor.
    Returns a tuple of (mock_connection, mock_cursor).
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    
    # Configure cursor to return itself when used as a context manager
    mock_cursor.__enter__.return_value = mock_cursor
    
    # Configure connection to return this cursor
    mock_conn.cursor.return_value = mock_cursor
    
    # Patch the get_connection method
    mocker.patch('backend.database.db.get_connection', return_value=mock_conn)
    
    return mock_conn, mock_cursor
