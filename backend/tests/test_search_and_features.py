"""
Test suite for Celebrity Buzz Index - Search Autocomplete and New Features
Tests:
1. Search autocomplete returns only celebrities (no plants, objects, albums)
2. Hot Celebs This Week banner displays correctly
3. Today's News shows major celebrity news (not gossip)
4. Team customization endpoint returns colors and icons
5. League share functionality
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSearchAutocomplete:
    """Test that autocomplete returns only celebrities, not plants/objects/albums"""
    
    def test_rihanna_returns_celebrity(self):
        """Rihanna search should return the singer"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=rihanna")
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        assert len(suggestions) >= 1, "Should return at least 1 result for Rihanna"
        
        # First result should be Rihanna the singer
        first = suggestions[0]
        assert "Rihanna" in first["name"], "First result should be Rihanna"
        assert "singer" in first["description"].lower() or "barbadian" in first["description"].lower(), \
            "Description should mention singer or Barbadian"
        assert first["image"], "Should have an image"
        assert first["estimated_tier"] in ["A", "B", "C", "D"], "Should have valid tier"
        assert first["estimated_price"] > 0, "Should have valid price"
    
    def test_beyonce_returns_celebrity(self):
        """Beyonce search should return the singer"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=beyonce")
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        assert len(suggestions) >= 1, "Should return at least 1 result for Beyonce"
        
        first = suggestions[0]
        assert "Beyoncé" in first["name"] or "Beyonce" in first["name"], "First result should be Beyoncé"
        assert "singer" in first["description"].lower() or "american" in first["description"].lower(), \
            "Description should mention singer or American"
    
    def test_kanye_returns_celebrity(self):
        """Kanye search should return Kanye West"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=kanye")
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        assert len(suggestions) >= 1, "Should return at least 1 result for Kanye"
        
        first = suggestions[0]
        assert "Kanye" in first["name"], "First result should be Kanye West"
        assert "rapper" in first["description"].lower() or "ye" in first["description"].lower(), \
            "Description should mention rapper"
    
    def test_holly_returns_only_celebrities_not_plants(self):
        """Holly search should return celebrities, NOT the Holly plant genus"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=holly")
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        # Check that no results are plants
        for suggestion in suggestions:
            desc_lower = suggestion["description"].lower()
            name_lower = suggestion["name"].lower()
            
            # Should NOT be a plant
            assert "genus" not in desc_lower, f"Should not return plant genus: {suggestion['name']}"
            assert "flowering plant" not in desc_lower, f"Should not return flowering plant: {suggestion['name']}"
            assert "species" not in desc_lower, f"Should not return species: {suggestion['name']}"
            
            # Should be a person
            person_indicators = ["actor", "actress", "singer", "presenter", "model", "skater", 
                               "born", "is a", "was a", "american", "british", "australian"]
            has_person_indicator = any(ind in desc_lower for ind in person_indicators)
            assert has_person_indicator, f"Should be a person: {suggestion['name']} - {suggestion['description'][:100]}"
    
    def test_short_query_returns_empty(self):
        """Queries less than 2 characters should return empty"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=a")
        assert response.status_code == 200
        data = response.json()
        assert data.get("suggestions", []) == [], "Short query should return empty"


class TestHotCelebsBanner:
    """Test Hot Celebs This Week banner endpoint"""
    
    def test_hot_celebs_endpoint_returns_200(self):
        """Hot celebs endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
    
    def test_hot_celebs_contains_expected_celebrities(self):
        """Hot celebs should contain major newsworthy celebrities"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        assert len(hot_celebs) >= 5, "Should have at least 5 hot celebs"
        
        # Check for expected celebrities
        names = [c["name"] for c in hot_celebs]
        
        # At least some of these should be present
        expected_celebs = ["Prince Andrew", "Meghan Markle", "Kanye West", "Taylor Swift", 
                          "Elon Musk", "Donald Trump", "Katie Price", "Holly Willoughby"]
        found_count = sum(1 for exp in expected_celebs if exp in names)
        assert found_count >= 4, f"Should have at least 4 expected hot celebs, found {found_count}: {names}"
    
    def test_hot_celebs_have_required_fields(self):
        """Each hot celeb should have required fields"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        for celeb in hot_celebs:
            assert "name" in celeb, f"Missing name: {celeb}"
            assert "tier" in celeb, f"Missing tier: {celeb}"
            assert "category" in celeb, f"Missing category: {celeb}"
            assert "hot_reason" in celeb, f"Missing hot_reason: {celeb}"
            assert "price" in celeb, f"Missing price: {celeb}"
            assert "image" in celeb, f"Missing image: {celeb}"
    
    def test_hot_celebs_have_reasons(self):
        """Each hot celeb should have a reason for being hot"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        for celeb in hot_celebs:
            reason = celeb.get("hot_reason", "")
            assert len(reason) > 5, f"Hot reason should be meaningful: {celeb['name']} - {reason}"


class TestTodaysNews:
    """Test Today's News endpoint - should show major news, not gossip"""
    
    def test_todays_news_endpoint_returns_200(self):
        """Today's news endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/todays-news")
        assert response.status_code == 200
    
    def test_todays_news_has_items(self):
        """Today's news should have news items"""
        response = requests.get(f"{BASE_URL}/api/todays-news")
        data = response.json()
        news = data.get("news", [])
        
        # May be empty if RSS feeds are down, but structure should be correct
        assert isinstance(news, list), "News should be a list"
    
    def test_todays_news_filters_gossip(self):
        """Today's news should not contain trivial gossip keywords"""
        response = requests.get(f"{BASE_URL}/api/todays-news")
        data = response.json()
        news = data.get("news", [])
        
        # Gossip keywords that should be filtered out
        gossip_keywords = ["braless", "bikini", "swimsuit", "beach body", "abs", "toned",
                         "shows off", "flaunts", "displays", "reveals figure"]
        
        for item in news:
            headline_lower = item.get("headline", "").lower()
            summary_lower = item.get("summary", "").lower()
            
            for keyword in gossip_keywords:
                assert keyword not in headline_lower, f"Gossip keyword '{keyword}' found in headline: {item['headline']}"
                assert keyword not in summary_lower, f"Gossip keyword '{keyword}' found in summary: {item['summary']}"
    
    def test_todays_news_has_required_fields(self):
        """Each news item should have required fields"""
        response = requests.get(f"{BASE_URL}/api/todays-news")
        data = response.json()
        news = data.get("news", [])
        
        for item in news:
            assert "headline" in item, f"Missing headline: {item}"
            assert "source" in item, f"Missing source: {item}"
            assert "summary" in item or "url" in item, f"Missing summary or url: {item}"


class TestTeamCustomization:
    """Test team customization options endpoint"""
    
    def test_customization_options_endpoint_returns_200(self):
        """Customization options endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/team/customization-options")
        assert response.status_code == 200
    
    def test_customization_options_has_colors(self):
        """Should return team colors"""
        response = requests.get(f"{BASE_URL}/api/team/customization-options")
        data = response.json()
        
        assert "colors" in data, "Should have colors"
        colors = data["colors"]
        assert len(colors) >= 5, "Should have at least 5 colors"
        
        # Check color structure
        for color in colors:
            assert "id" in color, f"Color missing id: {color}"
            assert "name" in color, f"Color missing name: {color}"
            assert "hex" in color, f"Color missing hex: {color}"
            assert color["hex"].startswith("#"), f"Hex should start with #: {color}"
    
    def test_customization_options_has_icons(self):
        """Should return team icons"""
        response = requests.get(f"{BASE_URL}/api/team/customization-options")
        data = response.json()
        
        assert "icons" in data, "Should have icons"
        icons = data["icons"]
        assert len(icons) >= 8, "Should have at least 8 icons"
        
        # Check icon structure
        for icon in icons:
            assert "id" in icon, f"Icon missing id: {icon}"
            assert "name" in icon, f"Icon missing name: {icon}"
            assert "emoji" in icon, f"Icon missing emoji: {icon}"
    
    def test_customization_options_specific_colors(self):
        """Should have specific expected colors"""
        response = requests.get(f"{BASE_URL}/api/team/customization-options")
        data = response.json()
        colors = data["colors"]
        
        color_ids = [c["id"] for c in colors]
        expected_colors = ["pink", "cyan", "gold", "purple", "red", "green", "orange", "white"]
        
        for expected in expected_colors:
            assert expected in color_ids, f"Missing expected color: {expected}"
    
    def test_customization_options_specific_icons(self):
        """Should have specific expected icons"""
        response = requests.get(f"{BASE_URL}/api/team/customization-options")
        data = response.json()
        icons = data["icons"]
        
        icon_ids = [i["id"] for i in icons]
        expected_icons = ["star", "crown", "fire", "lightning", "rocket", "diamond", "skull", "ghost"]
        
        for expected in expected_icons:
            assert expected in icon_ids, f"Missing expected icon: {expected}"


class TestLeagueEndpoints:
    """Test league-related endpoints"""
    
    def test_create_team_for_league_tests(self):
        """Create a test team for league tests"""
        response = requests.post(f"{BASE_URL}/api/team/create", json={
            "team_name": "TEST_LeagueTestTeam"
        })
        assert response.status_code == 200
        data = response.json()
        assert "team" in data
        return data["team"]["id"]
    
    def test_create_league(self):
        """Test creating a league"""
        # First create a team
        team_response = requests.post(f"{BASE_URL}/api/team/create", json={
            "team_name": "TEST_LeagueCreatorTeam"
        })
        team_id = team_response.json()["team"]["id"]
        
        # Create a league
        response = requests.post(f"{BASE_URL}/api/league/create", json={
            "name": "TEST_TestLeague",
            "team_id": team_id
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "league" in data
        league = data["league"]
        assert "id" in league
        assert "name" in league
        assert "code" in league
        assert len(league["code"]) == 6, "League code should be 6 characters"
        assert league["name"] == "TEST_TestLeague"
    
    def test_league_leaderboard(self):
        """Test league leaderboard endpoint"""
        # Create team and league
        team_response = requests.post(f"{BASE_URL}/api/team/create", json={
            "team_name": "TEST_LeaderboardTeam"
        })
        team_id = team_response.json()["team"]["id"]
        
        league_response = requests.post(f"{BASE_URL}/api/league/create", json={
            "name": "TEST_LeaderboardLeague",
            "team_id": team_id
        })
        league_id = league_response.json()["league"]["id"]
        
        # Get leaderboard
        response = requests.get(f"{BASE_URL}/api/league/{league_id}/leaderboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
