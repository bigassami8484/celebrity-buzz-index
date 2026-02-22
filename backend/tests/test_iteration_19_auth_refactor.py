"""
Iteration 19 - Auth Routes Refactoring Tests

Tests to verify that auth routes migrated from server.py to routes/auth.py
are working correctly.

Endpoints tested:
- GET /api/auth/me - Get current user info
- GET /api/categories - Get all categories
- GET /api/hot-celebs - Get hot celebrities
- GET /api/transfer-window-status - Get transfer window status
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuthRefactoring:
    """Test auth endpoints after refactoring to modular routes"""
    
    def test_auth_me_unauthenticated(self):
        """Test /api/auth/me returns proper response for unauthenticated user"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        # Should return 200 even for unauthenticated users
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "user" in data, "Response should contain 'user' field"
        assert "is_authenticated" in data, "Response should contain 'is_authenticated' field"
        assert data["user"] is None, "User should be null for unauthenticated request"
        assert data["is_authenticated"] is False, "is_authenticated should be false"
        
        print(f"✅ /api/auth/me returns correct unauthenticated response: {data}")
    
    def test_auth_me_with_invalid_token(self):
        """Test /api/auth/me with invalid bearer token"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_12345"}
        )
        
        # Should still return 200 with unauthenticated response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data["user"] is None, "User should be null for invalid token"
        assert data["is_authenticated"] is False, "is_authenticated should be false for invalid token"
        
        print(f"✅ /api/auth/me handles invalid token correctly: {data}")


class TestCategoriesEndpoint:
    """Test categories endpoint"""
    
    def test_categories_returns_9_categories(self):
        """Test /api/categories returns exactly 9 categories"""
        response = requests.get(f"{BASE_URL}/api/categories")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "categories" in data, "Response should contain 'categories' field"
        
        categories = data["categories"]
        assert len(categories) == 9, f"Expected 9 categories, got {len(categories)}"
        
        # Verify expected categories exist
        expected_ids = ["movie_stars", "tv_actors", "tv_personalities", "musicians", 
                       "athletes", "royals", "reality_tv", "public_figure", "other"]
        actual_ids = [cat["id"] for cat in categories]
        
        for expected_id in expected_ids:
            assert expected_id in actual_ids, f"Missing category: {expected_id}"
        
        # Verify each category has required fields
        for cat in categories:
            assert "id" in cat, "Category should have 'id' field"
            assert "name" in cat, "Category should have 'name' field"
            assert "icon" in cat, "Category should have 'icon' field"
        
        print(f"✅ /api/categories returns {len(categories)} categories: {actual_ids}")


class TestHotCelebsEndpoint:
    """Test hot celebs endpoint"""
    
    def test_hot_celebs_returns_list(self):
        """Test /api/hot-celebs returns celebrities list"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "hot_celebs" in data, "Response should contain 'hot_celebs' field"
        
        hot_celebs = data["hot_celebs"]
        assert isinstance(hot_celebs, list), "hot_celebs should be a list"
        assert len(hot_celebs) > 0, "hot_celebs should not be empty"
        
        # Verify each celeb has required fields
        for celeb in hot_celebs[:5]:  # Check first 5
            assert "name" in celeb, "Celebrity should have 'name' field"
            assert "tier" in celeb, "Celebrity should have 'tier' field"
            assert "price" in celeb, "Celebrity should have 'price' field"
            assert "category" in celeb, "Celebrity should have 'category' field"
        
        print(f"✅ /api/hot-celebs returns {len(hot_celebs)} celebrities")
        print(f"   Sample celebs: {[c['name'] for c in hot_celebs[:5]]}")
    
    def test_hot_celebs_have_news_premium(self):
        """Test hot celebs have news_premium indicator"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data["hot_celebs"]
        
        # Check that at least some celebs have news_premium
        celebs_with_premium = [c for c in hot_celebs if c.get("news_premium")]
        assert len(celebs_with_premium) > 0, "At least some celebs should have news_premium"
        
        print(f"✅ {len(celebs_with_premium)}/{len(hot_celebs)} celebs have news_premium")


class TestTransferWindowEndpoint:
    """Test transfer window status endpoint"""
    
    def test_transfer_window_status(self):
        """Test /api/transfer-window-status returns proper status"""
        response = requests.get(f"{BASE_URL}/api/transfer-window-status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Verify required fields
        assert "is_open" in data, "Response should contain 'is_open' field"
        assert isinstance(data["is_open"], bool), "is_open should be boolean"
        
        # Should have either next_window or current window info
        if not data["is_open"]:
            assert "next_window" in data, "Should have next_window when closed"
        
        print(f"✅ /api/transfer-window-status: is_open={data['is_open']}")
        if "next_window" in data:
            print(f"   Next window: {data['next_window']}")


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self):
        """Test /api/health returns OK"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("status") == "healthy", f"Expected healthy status, got {data}"
        
        print(f"✅ /api/health returns healthy status")


class TestAuthRouterIntegration:
    """Test that auth router is properly integrated with main app"""
    
    def test_auth_logout_endpoint_exists(self):
        """Test /api/auth/logout endpoint exists"""
        response = requests.post(f"{BASE_URL}/api/auth/logout")
        
        # Should return 200 even without session
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "success" in data, "Response should contain 'success' field"
        
        print(f"✅ /api/auth/logout endpoint works: {data}")
    
    def test_auth_magic_link_send_validation(self):
        """Test /api/auth/magic-link/send validates email"""
        # Test with invalid email
        response = requests.post(
            f"{BASE_URL}/api/auth/magic-link/send",
            json={"email": "invalid-email"}
        )
        
        # Should return 422 for validation error
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"
        
        print(f"✅ /api/auth/magic-link/send validates email correctly")
    
    def test_auth_magic_link_send_valid_email(self):
        """Test /api/auth/magic-link/send with valid email"""
        response = requests.post(
            f"{BASE_URL}/api/auth/magic-link/send",
            json={"email": "test@example.com"}
        )
        
        # Should return 200 for valid email
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "success" in data, "Response should contain 'success' field"
        assert data["success"] is True, "success should be True"
        
        print(f"✅ /api/auth/magic-link/send works with valid email")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
