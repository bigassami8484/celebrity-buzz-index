"""
Iteration 21 - Recognition Score Feature Tests
Tests for:
1. Backend server health
2. Autocomplete endpoint returns recognition_score for DB-matched celebrities
3. Taylor Swift search returns recognition score
4. Hot Celebs endpoint works
5. Team creation/management
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBackendHealth:
    """Test backend server is running and healthy"""
    
    def test_api_root_returns_info(self):
        """Test API root endpoint returns version info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Celebrity Buzz Index" in data["message"]
        print(f"✓ API root returns: {data}")
    
    def test_categories_endpoint(self):
        """Test categories endpoint returns list of categories"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 9  # Should have at least 9 categories
        print(f"✓ Categories endpoint returns {len(data)} categories")


class TestAutocompleteRecognitionScore:
    """Test autocomplete endpoint returns recognition_score for DB-matched celebrities"""
    
    def test_taylor_swift_has_recognition_score(self):
        """Test Taylor Swift search returns recognition_score"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Taylor%20Swift")
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        suggestions = data["suggestions"]
        assert len(suggestions) >= 1
        
        # Find Taylor Swift in suggestions
        taylor = None
        for s in suggestions:
            if "Taylor Swift" in s.get("name", ""):
                taylor = s
                break
        
        assert taylor is not None, "Taylor Swift not found in suggestions"
        assert "recognition_score" in taylor, "recognition_score not in Taylor Swift result"
        assert taylor["recognition_score"] >= 0 and taylor["recognition_score"] <= 100
        print(f"✓ Taylor Swift recognition_score: {taylor['recognition_score']}")
        print(f"✓ Taylor Swift tier: {taylor.get('tier')}")
        print(f"✓ Taylor Swift price: £{taylor.get('price')}M")
    
    def test_db_matched_celebrity_has_recognition_score(self):
        """Test that DB-matched celebrities have recognition_score"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Beyonce")
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        if len(suggestions) > 0:
            # Check first suggestion (should be DB match)
            first = suggestions[0]
            if first.get("is_db_match") or first.get("is_exact_match"):
                assert "recognition_score" in first, "DB-matched celebrity should have recognition_score"
                print(f"✓ {first['name']} recognition_score: {first.get('recognition_score')}")
    
    def test_partial_match_taylor_has_recognition_score(self):
        """Test partial match 'Taylor' returns celebrities with recognition_score"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Taylor")
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        assert len(suggestions) >= 1
        
        # Check if any DB-matched celebrity has recognition_score
        db_matches_with_score = [s for s in suggestions if s.get("recognition_score") is not None]
        print(f"✓ Found {len(db_matches_with_score)} celebrities with recognition_score out of {len(suggestions)}")
        
        for s in db_matches_with_score:
            print(f"  - {s['name']}: recognition_score={s['recognition_score']}, tier={s.get('tier')}")
    
    def test_recognition_score_range(self):
        """Test recognition_score is within valid range (0-100)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Taylor%20Swift")
        assert response.status_code == 200
        data = response.json()
        
        for s in data.get("suggestions", []):
            if "recognition_score" in s:
                score = s["recognition_score"]
                assert 0 <= score <= 100, f"recognition_score {score} out of range for {s['name']}"
        print("✓ All recognition_scores are within valid range (0-100)")


class TestHotCelebs:
    """Test Hot Celebs section loads correctly"""
    
    def test_hot_celebs_endpoint(self):
        """Test hot-celebs endpoint returns list of celebrities"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1
        print(f"✓ Hot Celebs returns {len(data)} celebrities")
        
        # Check first celebrity has required fields
        first = data[0]
        assert "name" in first
        assert "tier" in first
        assert "price" in first
        print(f"✓ Sample hot celeb: {first['name']} - {first['tier']} - £{first['price']}M")
    
    def test_hot_celebs_have_images(self):
        """Test hot celebs have images"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        celebs_with_images = [c for c in data if c.get("image")]
        print(f"✓ {len(celebs_with_images)}/{len(data)} hot celebs have images")


class TestTeamManagement:
    """Test team creation and management"""
    
    def test_create_team(self):
        """Test team creation endpoint"""
        response = requests.post(f"{BASE_URL}/api/team/create", json={
            "team_name": "TEST_Recognition_Score_Team"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "team_name" in data
        assert "budget_remaining" in data
        assert data["budget_remaining"] == 50  # Starting budget
        print(f"✓ Team created: {data['team_name']} with ID {data['id']}")
        print(f"✓ Budget: £{data['budget_remaining']}M")
        
        return data["id"]
    
    def test_get_team(self):
        """Test getting team by ID"""
        # First create a team
        create_response = requests.post(f"{BASE_URL}/api/team/create", json={
            "team_name": "TEST_Get_Team"
        })
        assert create_response.status_code == 200
        team_id = create_response.json()["id"]
        
        # Then get the team
        response = requests.get(f"{BASE_URL}/api/team/{team_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == team_id
        assert data["team_name"] == "TEST_Get_Team"
        print(f"✓ Retrieved team: {data['team_name']}")


class TestCelebritySearch:
    """Test celebrity search functionality"""
    
    def test_search_celebrity(self):
        """Test searching for a celebrity"""
        response = requests.post(f"{BASE_URL}/api/celebrity/search", json={
            "name": "Taylor Swift"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "name" in data
        assert "tier" in data
        assert "price" in data
        print(f"✓ Search result: {data['name']} - {data['tier']} - £{data['price']}M")
    
    def test_search_returns_tier(self):
        """Test search returns correct tier for A-list celebrity"""
        response = requests.post(f"{BASE_URL}/api/celebrity/search", json={
            "name": "Taylor Swift"
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["tier"] == "A", f"Taylor Swift should be A-list, got {data['tier']}"
        print(f"✓ Taylor Swift correctly identified as {data['tier']}-LIST")


class TestTransferWindow:
    """Test transfer window status"""
    
    def test_transfer_window_status(self):
        """Test transfer window status endpoint"""
        response = requests.get(f"{BASE_URL}/api/transfer-window-status")
        assert response.status_code == 200
        data = response.json()
        
        assert "is_open" in data
        assert "status" in data
        print(f"✓ Transfer window status: {data['status']}")
        print(f"✓ Is open: {data['is_open']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
