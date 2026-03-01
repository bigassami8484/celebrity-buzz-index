"""
Test iteration 14 - Price consistency fix and Hot Celebs Banner
Tests:
1. Hot Celebs banner returns celebs with photos, names, tiers, prices
2. Price consistency when adding celebrity to team (same as card price)
3. Budget correctly deducted when adding celeb
"""
import pytest
import requests
import os
import re

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHotCelebsBanner:
    """Test Hot Celebs Banner functionality"""
    
    def test_hot_celebs_endpoint_returns_data(self):
        """Test that hot-celebs endpoint returns celebrity data"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        
        data = response.json()
        assert "hot_celebs" in data
        assert len(data["hot_celebs"]) > 0
        print(f"✅ Hot Celebs endpoint returns {len(data['hot_celebs'])} celebrities")
    
    def test_hot_celebs_have_required_fields(self):
        """Test that each hot celeb has name, tier, price, image"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        
        data = response.json()
        for celeb in data["hot_celebs"]:
            assert "name" in celeb, f"Missing name for celeb"
            assert "tier" in celeb, f"Missing tier for {celeb.get('name')}"
            assert "price" in celeb, f"Missing price for {celeb.get('name')}"
            assert "image" in celeb, f"Missing image for {celeb.get('name')}"
            assert "hot_reason" in celeb, f"Missing hot_reason for {celeb.get('name')}"
            
            # Validate tier is valid
            assert celeb["tier"] in ["A", "B", "C", "D"], f"Invalid tier {celeb['tier']} for {celeb['name']}"
            
            # Validate price is within tier range
            tier = celeb["tier"]
            price = celeb["price"]
            if tier == "A":
                assert 9.0 <= price <= 12.0, f"A-list price {price} out of range for {celeb['name']}"
            elif tier == "B":
                assert 5.0 <= price <= 8.0, f"B-list price {price} out of range for {celeb['name']}"
            elif tier == "C":
                assert 2.0 <= price <= 4.0, f"C-list price {price} out of range for {celeb['name']}"
            elif tier == "D":
                assert 0.5 <= price <= 1.5, f"D-list price {price} out of range for {celeb['name']}"
        
        print(f"✅ All {len(data['hot_celebs'])} hot celebs have required fields with valid values")


class TestPriceConsistency:
    """Test price consistency when adding celebrities to team"""
    
    @pytest.fixture
    def test_team(self):
        """Create a test team for price testing"""
        response = requests.post(
            f"{BASE_URL}/api/team/create",
            json={"team_name": "TEST_Price_Consistency_Team"}
        )
        assert response.status_code == 200
        team = response.json()["team"]
        yield team
        # Cleanup - no explicit delete endpoint, team will be orphaned
    
    def test_search_celebrity_returns_price(self):
        """Test that searching for a celebrity returns a price"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Leonardo DiCaprio"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "celebrity" in data
        celeb = data["celebrity"]
        
        assert "price" in celeb
        assert "tier" in celeb
        assert celeb["price"] > 0
        
        print(f"✅ Leonardo DiCaprio search: tier={celeb['tier']}, price=£{celeb['price']}M")
        return celeb
    
    def test_add_to_team_uses_same_price_as_search(self, test_team):
        """Test that adding to team uses the same price as shown in search"""
        # First search for a celebrity
        search_response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Tom Hanks"}
        )
        assert search_response.status_code == 200
        celeb = search_response.json()["celebrity"]
        search_price = celeb["price"]
        celeb_id = celeb["id"]
        celeb_tier = celeb["tier"]
        
        print(f"Search result: {celeb['name']} - tier={celeb_tier}, price=£{search_price}M")
        
        # Get initial budget
        initial_budget = test_team["budget_remaining"]
        
        # Add to team
        add_response = requests.post(
            f"{BASE_URL}/api/team/add",
            json={"team_id": test_team["id"], "celebrity_id": celeb_id}
        )
        assert add_response.status_code == 200
        
        updated_team = add_response.json()["team"]
        
        # Find the added celebrity in team
        added_celeb = None
        for tc in updated_team["celebrities"]:
            if tc["celebrity_id"] == celeb_id:
                added_celeb = tc
                break
        
        assert added_celeb is not None, "Celebrity not found in team after adding"
        team_price = added_celeb["price"]
        
        print(f"Team panel price: £{team_price}M")
        
        # CRITICAL: Verify price consistency
        # The price in team should match the search price (using same calculation)
        # Allow small tolerance for floating point
        assert abs(team_price - search_price) < 0.1, \
            f"PRICE MISMATCH: Search showed £{search_price}M but team shows £{team_price}M"
        
        print(f"✅ PRICE MATCH: Search (£{search_price}M) = Team (£{team_price}M)")
        
        # Verify budget was correctly deducted
        expected_budget = initial_budget - team_price
        actual_budget = updated_team["budget_remaining"]
        
        assert abs(actual_budget - expected_budget) < 0.1, \
            f"Budget mismatch: expected £{expected_budget}M, got £{actual_budget}M"
        
        print(f"✅ Budget correctly deducted: £{initial_budget}M - £{team_price}M = £{actual_budget}M")
    
    def test_hot_celeb_price_matches_search_price(self):
        """Test that Hot Celebs prices match what you get when searching"""
        # Get hot celebs
        hot_response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert hot_response.status_code == 200
        hot_celebs = hot_response.json()["hot_celebs"]
        
        # Test first hot celeb
        if len(hot_celebs) > 0:
            hot_celeb = hot_celebs[0]
            hot_price = hot_celeb["price"]
            hot_name = hot_celeb["name"]
            
            print(f"Hot Celeb: {hot_name} - £{hot_price}M")
            
            # Search for the same celebrity
            search_response = requests.post(
                f"{BASE_URL}/api/celebrity/search",
                json={"name": hot_name}
            )
            assert search_response.status_code == 200
            
            search_celeb = search_response.json()["celebrity"]
            search_price = search_celeb["price"]
            
            print(f"Search result: {search_celeb['name']} - £{search_price}M")
            
            # Prices should match (both use default_buzz=50)
            assert abs(hot_price - search_price) < 0.5, \
                f"PRICE MISMATCH: Hot Celeb shows £{hot_price}M but search shows £{search_price}M"
            
            print(f"✅ PRICE MATCH: Hot Celeb (£{hot_price}M) ≈ Search (£{search_price}M)")


class TestBudgetDeduction:
    """Test budget is correctly deducted when adding celebrities"""
    
    @pytest.fixture
    def fresh_team(self):
        """Create a fresh team with £50M budget"""
        response = requests.post(
            f"{BASE_URL}/api/team/create",
            json={"team_name": "TEST_Budget_Team"}
        )
        assert response.status_code == 200
        team = response.json()["team"]
        assert team["budget_remaining"] == 50, "New team should have £50M budget"
        yield team
    
    def test_budget_deduction_matches_displayed_price(self, fresh_team):
        """Test that budget deduction equals the displayed price"""
        # Search for a celebrity
        search_response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Brad Pitt"}
        )
        assert search_response.status_code == 200
        celeb = search_response.json()["celebrity"]
        displayed_price = celeb["price"]
        
        print(f"Brad Pitt displayed price: £{displayed_price}M")
        
        # Add to team
        add_response = requests.post(
            f"{BASE_URL}/api/team/add",
            json={"team_id": fresh_team["id"], "celebrity_id": celeb["id"]}
        )
        assert add_response.status_code == 200
        
        updated_team = add_response.json()["team"]
        new_budget = updated_team["budget_remaining"]
        
        # Calculate expected budget
        expected_budget = 50 - displayed_price
        
        assert abs(new_budget - expected_budget) < 0.1, \
            f"Budget mismatch: expected £{expected_budget}M (50 - {displayed_price}), got £{new_budget}M"
        
        print(f"✅ Budget correctly deducted: £50M - £{displayed_price}M = £{new_budget}M")


class TestLeonardoDiCaprioPriceFix:
    """Specific test for Leonardo DiCaprio price fix mentioned in bug report"""
    
    @pytest.fixture
    def test_team(self):
        """Create a test team"""
        response = requests.post(
            f"{BASE_URL}/api/team/create",
            json={"team_name": "TEST_DiCaprio_Team"}
        )
        assert response.status_code == 200
        yield response.json()["team"]
    
    def test_leonardo_dicaprio_price_consistency(self, test_team):
        """
        Bug report: Leonardo DiCaprio showing 10.3M on card but 19M when added
        This test verifies the fix - prices should now match
        """
        # Search for Leonardo DiCaprio
        search_response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Leonardo DiCaprio"}
        )
        assert search_response.status_code == 200
        celeb = search_response.json()["celebrity"]
        
        card_price = celeb["price"]
        celeb_tier = celeb["tier"]
        
        print(f"Leonardo DiCaprio card: tier={celeb_tier}, price=£{card_price}M")
        
        # Verify price is within A-list range (he should be A-list)
        assert celeb_tier == "A", f"Leonardo DiCaprio should be A-list, got {celeb_tier}"
        assert 9.0 <= card_price <= 12.0, f"A-list price should be £9-12M, got £{card_price}M"
        
        # Add to team
        add_response = requests.post(
            f"{BASE_URL}/api/team/add",
            json={"team_id": test_team["id"], "celebrity_id": celeb["id"]}
        )
        assert add_response.status_code == 200
        
        updated_team = add_response.json()["team"]
        
        # Find Leonardo in team
        leo_in_team = None
        for tc in updated_team["celebrities"]:
            if "Leonardo" in tc["name"]:
                leo_in_team = tc
                break
        
        assert leo_in_team is not None, "Leonardo DiCaprio not found in team"
        team_price = leo_in_team["price"]
        
        print(f"Leonardo DiCaprio in team: price=£{team_price}M")
        
        # CRITICAL: Verify the bug is fixed - prices should match
        assert abs(card_price - team_price) < 0.1, \
            f"BUG NOT FIXED: Card shows £{card_price}M but team shows £{team_price}M"
        
        # Verify it's NOT the old buggy price of £19M
        assert team_price < 15, f"Price £{team_price}M is too high - old bug may still exist"
        
        print(f"✅ BUG FIXED: Leonardo DiCaprio price consistent - Card (£{card_price}M) = Team (£{team_price}M)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
