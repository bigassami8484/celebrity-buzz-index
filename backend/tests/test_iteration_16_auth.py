"""
Iteration 16 Tests: Title Size and Auth Implementation
Tests for:
1. /api/auth/me endpoint returns correct response when not logged in
2. Backend health and basic endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_auth_me_unauthenticated(self):
        """Test /api/auth/me returns correct response when not logged in"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        # Should return 200 with user: null
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "user" in data, "Response should contain 'user' field"
        assert "is_authenticated" in data, "Response should contain 'is_authenticated' field"
        assert data["user"] is None, "User should be null when not authenticated"
        assert data["is_authenticated"] == False, "is_authenticated should be False"
        
    def test_auth_logout_without_session(self):
        """Test /api/auth/logout works without active session"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        
        # Should return 200 even without session
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("success") == True, "Logout should return success: true"


class TestBasicEndpoints:
    """Test basic API endpoints are working"""
    
    def test_categories_endpoint(self):
        """Test /api/categories returns data"""
        response = requests.get(f"{BASE_URL}/api/categories")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Categories should return a list"
        assert len(data) > 0, "Should have at least one category"
        
    def test_celebrities_search(self):
        """Test /api/celebrities search endpoint"""
        response = requests.get(f"{BASE_URL}/api/celebrities?search=taylor")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "celebrities" in data, "Response should contain 'celebrities' field"
        
    def test_hot_celebs_endpoint(self):
        """Test /api/hot-celebs returns data"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Hot celebs should return a list"
        
    def test_stats_endpoint(self):
        """Test /api/stats returns data"""
        response = requests.get(f"{BASE_URL}/api/stats")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, dict), "Stats should return a dictionary"


class TestMagicLinkEndpoint:
    """Test magic link authentication endpoints"""
    
    def test_magic_link_send_invalid_email(self):
        """Test magic link send with invalid email format"""
        response = requests.post(
            f"{BASE_URL}/api/auth/magic-link/send",
            json={"email": "invalid-email"}
        )
        
        # Should return 422 for invalid email format
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"
        
    def test_magic_link_verify_invalid_token(self):
        """Test magic link verify with invalid token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/magic-link/verify",
            json={"token": "invalid-token-12345"}
        )
        
        # Should return 400 or 404 for invalid token
        assert response.status_code in [400, 404], f"Expected 400 or 404, got {response.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
