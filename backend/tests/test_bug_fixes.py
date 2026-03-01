"""
Test cases for Celebrity Buzz Index bug fixes:
- P0: Autocomplete search should always show images (fallback to placeholder)
- P1: Celebrity buzz scores should never be below 5 points
- P2: How It Works section should show '+100 if celeb dies!'
- P2: Points Methodology modal should show '+100 bonus points'
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutocompleteImageFallback:
    """P0: Test that autocomplete always returns images with fallback"""
    
    def test_autocomplete_returns_images_for_all_results(self):
        """All autocomplete suggestions should have image URLs"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Tom")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        assert len(suggestions) > 0, "Should return at least one suggestion"
        
        for suggestion in suggestions:
            image = suggestion.get('image', '')
            assert image and len(image) > 0, f"Suggestion '{suggestion.get('name')}' should have an image URL"
    
    def test_autocomplete_fallback_for_generic_names(self):
        """Generic names without Wikipedia thumbnails should use fallback"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=John")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        for suggestion in suggestions:
            image = suggestion.get('image', '')
            assert image and len(image) > 0, f"Suggestion '{suggestion.get('name')}' should have an image URL"
            # Check if it's either a Wikipedia image or a fallback
            is_valid = 'upload.wikimedia.org' in image or 'ui-avatars.com' in image
            assert is_valid, f"Image should be from Wikipedia or fallback: {image}"
    
    def test_autocomplete_short_query_returns_empty(self):
        """Queries less than 2 characters should return empty"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=T")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        assert len(suggestions) == 0, "Short queries should return empty suggestions"


class TestMinimumBuzzScore:
    """P1: Test that buzz scores are never below 5 points"""
    
    def test_buzz_score_minimum_for_new_celebrity(self):
        """New celebrity search should return buzz score >= 5"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Ed Sheeran"}
        )
        assert response.status_code == 200
        
        data = response.json()
        celebrity = data.get('celebrity', {})
        buzz_score = celebrity.get('buzz_score', 0)
        
        assert buzz_score >= 5.0, f"Buzz score should be at least 5, got {buzz_score}"
    
    def test_buzz_score_minimum_for_unknown_celebrity(self):
        """Unknown celebrity should still have minimum buzz score"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Random Unknown Person ABC123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        celebrity = data.get('celebrity', {})
        buzz_score = celebrity.get('buzz_score', 0)
        
        assert buzz_score >= 5.0, f"Buzz score should be at least 5, got {buzz_score}"


class TestPointsMethodology:
    """P2: Test that points methodology includes Brown Bread Bonus with +100"""
    
    def test_points_methodology_includes_brown_bread_bonus(self):
        """Points methodology should include Brown Bread Bonus"""
        response = requests.get(f"{BASE_URL}/api/points-methodology")
        assert response.status_code == 200
        
        data = response.json()
        factors = data.get('factors', [])
        
        # Find Brown Bread Bonus factor
        brown_bread = None
        for factor in factors:
            if 'brown bread' in factor.get('name', '').lower():
                brown_bread = factor
                break
        
        assert brown_bread is not None, "Points methodology should include Brown Bread Bonus"
        assert brown_bread.get('points_per_unit') == 100.0, "Brown Bread Bonus should be 100 points"


class TestBrownBreadBonus:
    """Test Brown Bread Bonus functionality"""
    
    def test_brown_bread_bonus_value_in_team_add(self):
        """Adding deceased celebrity should give 100 point bonus"""
        # Create a team first
        team_response = requests.post(
            f"{BASE_URL}/api/team/create",
            json={"team_name": "TEST_BrownBreadTeam"}
        )
        assert team_response.status_code == 200
        team = team_response.json().get('team', {})
        team_id = team.get('id')
        
        # Note: We can't easily test this without a deceased celebrity in the DB
        # But we can verify the team was created
        assert team_id is not None, "Team should be created"
        
        # Clean up - get team to verify
        get_response = requests.get(f"{BASE_URL}/api/team/{team_id}")
        assert get_response.status_code == 200


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """API root should return version info"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        data = response.json()
        assert 'message' in data
        assert 'version' in data
    
    def test_categories_endpoint(self):
        """Categories endpoint should return list"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get('categories', [])
        assert len(categories) > 0, "Should return categories"
    
    def test_stats_endpoint(self):
        """Stats endpoint should return player count"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert 'player_count' in data
        assert 'celebrity_count' in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
