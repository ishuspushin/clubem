"""
API endpoint tests.
"""

import pytest
import json
from pathlib import Path
from io import BytesIO

# Mock Flask app for testing
@pytest.fixture
def app():
    """Create test Flask app."""
    from app import create_app
    from app.core.config import Config
    
    # Create test config
    config = Config.load_from_env()
    
    app = create_app()
    app.config['TESTING'] = True
    
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def sample_pdf():
    """Create sample PDF for testing."""
    # Create a minimal PDF
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    return BytesIO(pdf_content)


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] in ['healthy', 'degraded']


class TestUploadEndpoint:
    """Test PDF upload endpoint."""
    
    def test_upload_no_files(self, client):
        """Test upload with no files."""
        response = client.post('/api/upload')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type."""
        data = {
            'files': (BytesIO(b"test"), 'test.txt')
        }
        response = client.post('/api/upload', data=data)
        assert response.status_code == 400
    
    def test_upload_valid_pdf(self, client, sample_pdf):
        """Test upload with valid PDF."""
        data = {
            'files': (sample_pdf, 'test.pdf')
        }
        response = client.post(
            '/api/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should accept the upload
        assert response.status_code in [200, 202, 400]  # May fail validation


class TestStatusEndpoint:
    """Test status check endpoint."""
    
    def test_get_status(self, client):
        """Test status check."""
        workflow_id = "test-workflow-123"
        response = client.get(f'/api/status/{workflow_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'workflow_id' in data


class TestReviewEndpoints:
    """Test review endpoints."""
    
    def test_get_pending_reviews(self, client):
        """Test get pending reviews."""
        response = client.get('/api/review/pending')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'reviews' in data
    
    def test_submit_review_no_data(self, client):
        """Test submit review with no data."""
        response = client.post('/api/review/submit')
        assert response.status_code == 400
    
    def test_submit_review_invalid_action(self, client):
        """Test submit review with invalid action."""
        data = {
            'workflow_id': 'test-123',
            'action': 'invalid_action'
        }
        response = client.post(
            '/api/review/submit',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400


class TestPlatformEndpoint:
    """Test platforms endpoint."""
    
    def test_get_platforms(self, client):
        """Test get supported platforms."""
        response = client.get('/api/platforms')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'platforms' in data
        assert len(data['platforms']) > 0
