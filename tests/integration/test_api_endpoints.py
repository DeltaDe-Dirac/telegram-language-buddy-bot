import pytest
import json
import sys
import os

# Add the src directory to the Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.mark.integration
class TestAPIEndpoints:
    """Integration tests for Flask API endpoints"""

    def test_home_endpoint(self, client):
        """Test the home endpoint returns success"""
        response = client.get('/')
        assert response.status_code == 200
        assert b"Language Buddy Bot" in response.data

    def test_set_webhook_missing_url(self, client):
        """Test set_webhook endpoint with missing URL"""
        response = client.post('/set_webhook')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_set_webhook_success(self, client):
        """Test set_webhook endpoint with valid URL"""
        response = client.post('/set_webhook', json={"url": "https://example.com/webhook"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "success" in data

    def test_manual_translate_missing_data(self, client):
        """Test manual translate endpoint with missing data"""
        response = client.post('/translate')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_manual_translate_success(self, client):
        """Test manual translate endpoint with valid data"""
        test_data = {
            "text": "Hello world",
            "source_lang": "en",
            "target_lang": "es"
        }
        response = client.post('/translate', json=test_data)
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "translated_text" in data

    def test_stats_endpoint(self, client):
        """Test stats endpoint"""
        response = client.get('/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "stats" in data

    def test_voice_status_endpoint(self, client):
        """Test voice status endpoint"""
        response = client.get('/voice-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "voice_services" in data
