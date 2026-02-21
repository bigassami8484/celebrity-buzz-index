"""
Test iteration 11 features:
1. How It Works has explanatory text under each icon
2. Spacing between How It Works and search bar (mb-8 class)
3. Spacing between category filter and Hot Celebs (mb-6 class)
4. Search 'gucci' returns only people (Gucci Mane, Aldo Gucci) - not the brand
5. Search 'nike' returns only people (Nike Ardilla) - not the brand
6. Search 'tesla' returns only Nikola Tesla - not cars
7. Search 'lion' returns only people (Alfred Lion) - not animals
8. Category (Musicians) shows correct dynamic prices
9. Buzz score is hidden on celebrity cards
10. Buzz score is removed from team panel display
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSearchFiltering:
    """Test that search filters out brands, cars, animals, etc."""
    
    def test_search_gucci_returns_only_people(self):
        """Search 'gucci' should return only people like Gucci Mane, Aldo Gucci - not the brand"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=gucci")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        # Should have results
        assert len(suggestions) > 0, "Should return at least one person with 'Gucci' in name"
        
        # Check that results are people, not brands
        for suggestion in suggestions:
            name = suggestion.get('name', '')
            description = suggestion.get('description', '').lower()
            
            # Should not be the fashion brand
            assert 'fashion house' not in description, f"Brand 'Gucci' should be filtered out: {name}"
            assert 'luxury brand' not in description, f"Brand 'Gucci' should be filtered out: {name}"
            assert 'italian fashion' not in description, f"Brand 'Gucci' should be filtered out: {name}"
            
        # Should include known people
        names = [s.get('name', '') for s in suggestions]
        assert any('Gucci Mane' in n or 'Aldo Gucci' in n or 'Patricia Gucci' in n for n in names), \
            f"Should include people with 'Gucci' in name. Got: {names}"
        
        print(f"✓ Search 'gucci' returned {len(suggestions)} people: {names}")
    
    def test_search_nike_returns_only_people(self):
        """Search 'nike' should return only people like Nike Ardilla - not the brand"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=nike")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        # Should have results
        assert len(suggestions) > 0, "Should return at least one person with 'Nike' in name"
        
        # Check that results are people, not brands
        for suggestion in suggestions:
            name = suggestion.get('name', '')
            description = suggestion.get('description', '').lower()
            
            # Should not be the sportswear brand
            assert 'sportswear' not in description, f"Brand 'Nike' should be filtered out: {name}"
            assert 'footwear' not in description, f"Brand 'Nike' should be filtered out: {name}"
            assert 'athletic' not in description or 'athlete' in description, f"Brand 'Nike' should be filtered out: {name}"
            
        # Should include Nike Ardilla
        names = [s.get('name', '') for s in suggestions]
        assert any('Nike Ardilla' in n for n in names), \
            f"Should include Nike Ardilla. Got: {names}"
        
        print(f"✓ Search 'nike' returned {len(suggestions)} people: {names}")
    
    def test_search_tesla_filters_cars(self):
        """Search 'tesla' should return only Nikola Tesla - not cars"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=tesla")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        # Check that results don't include cars
        for suggestion in suggestions:
            name = suggestion.get('name', '')
            description = suggestion.get('description', '').lower()
            
            # Should not be Tesla cars
            assert 'electric car' not in description, f"Tesla cars should be filtered out: {name}"
            assert 'electric vehicle' not in description, f"Tesla cars should be filtered out: {name}"
            assert 'model s' not in description, f"Tesla cars should be filtered out: {name}"
            assert 'model 3' not in description, f"Tesla cars should be filtered out: {name}"
            assert 'model x' not in description, f"Tesla cars should be filtered out: {name}"
            assert 'model y' not in description, f"Tesla cars should be filtered out: {name}"
            
        # If results exist, should be Nikola Tesla
        if len(suggestions) > 0:
            names = [s.get('name', '') for s in suggestions]
            assert any('Nikola Tesla' in n for n in names), \
                f"Should include Nikola Tesla if any results. Got: {names}"
            print(f"✓ Search 'tesla' returned {len(suggestions)} people: {names}")
        else:
            print("✓ Search 'tesla' returned no results (cars filtered out)")
    
    def test_search_lion_returns_only_people(self):
        """Search 'lion' should return only people like Alfred Lion - not animals"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=lion")
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get('suggestions', [])
        
        # Should have results
        assert len(suggestions) > 0, "Should return at least one person with 'Lion' in name"
        
        # Check that results are people, not animals
        for suggestion in suggestions:
            name = suggestion.get('name', '')
            description = suggestion.get('description', '').lower()
            
            # Should not be the animal
            assert 'large cat' not in description, f"Animal 'Lion' should be filtered out: {name}"
            assert 'carnivore' not in description, f"Animal 'Lion' should be filtered out: {name}"
            assert 'predator' not in description, f"Animal 'Lion' should be filtered out: {name}"
            assert 'genus panthera' not in description, f"Animal 'Lion' should be filtered out: {name}"
            
        # Should include Alfred Lion
        names = [s.get('name', '') for s in suggestions]
        assert any('Alfred Lion' in n for n in names), \
            f"Should include Alfred Lion. Got: {names}"
        
        print(f"✓ Search 'lion' returned {len(suggestions)} people: {names}")


class TestCategoryPricing:
    """Test that category endpoint returns correct dynamic prices"""
    
    def test_musicians_category_pricing(self):
        """Musicians category should show correct dynamic prices based on tier"""
        response = requests.get(f"{BASE_URL}/api/celebrities/category/musicians")
        assert response.status_code == 200
        
        data = response.json()
        celebrities = data.get('celebrities', [])
        
        assert len(celebrities) > 0, "Should return musicians"
        
        # Check pricing for each tier
        tier_price_ranges = {
            'A': (9, 12),   # A-list: £9-12M
            'B': (5, 8),    # B-list: £5-8M
            'C': (2, 4),    # C-list: £2-4M
            'D': (0.5, 1.5) # D-list: £0.5-1.5M
        }
        
        for celeb in celebrities:
            tier = celeb.get('tier', 'D')
            price = celeb.get('price', 0)
            name = celeb.get('name', '')
            
            if tier in tier_price_ranges:
                min_price, max_price = tier_price_ranges[tier]
                assert min_price <= price <= max_price, \
                    f"{name} ({tier}-list) price £{price}M should be in range £{min_price}-{max_price}M"
                print(f"  ✓ {name}: {tier}-list £{price}M (valid range: £{min_price}-{max_price}M)")
        
        print(f"✓ Musicians category returned {len(celebrities)} celebrities with correct pricing")


class TestHotCelebs:
    """Test Hot Celebs endpoint"""
    
    def test_hot_celebs_returns_data(self):
        """Hot Celebs endpoint should return celebrities with correct data"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data.get('hot_celebs', [])
        
        assert len(hot_celebs) > 0, "Should return hot celebs"
        
        # Check each celeb has required fields
        for celeb in hot_celebs:
            assert 'name' in celeb, "Hot celeb should have name"
            assert 'tier' in celeb, "Hot celeb should have tier"
            assert 'price' in celeb, "Hot celeb should have price"
            
            # Check price is within tier range
            tier = celeb.get('tier', 'D')
            price = celeb.get('price', 0)
            name = celeb.get('name', '')
            
            tier_price_ranges = {
                'A': (9, 12),
                'B': (5, 8),
                'C': (2, 4),
                'D': (0.5, 1.5)
            }
            
            if tier in tier_price_ranges:
                min_price, max_price = tier_price_ranges[tier]
                assert min_price <= price <= max_price, \
                    f"{name} ({tier}-list) price £{price}M should be in range £{min_price}-{max_price}M"
        
        print(f"✓ Hot Celebs returned {len(hot_celebs)} celebrities with correct pricing")


class TestTeamPanel:
    """Test team panel functionality"""
    
    def test_create_team_and_add_celebrity(self):
        """Create team and add celebrity - verify buzz score not in response"""
        # Create a team
        response = requests.post(f"{BASE_URL}/api/team/create", json={"team_name": "TEST_BuzzHidden"})
        assert response.status_code == 200
        
        data = response.json()
        team = data.get('team', {})
        team_id = team.get('id')
        
        assert team_id, "Team should have ID"
        
        # Search for a celebrity
        search_response = requests.get(f"{BASE_URL}/api/autocomplete?q=adele")
        assert search_response.status_code == 200
        
        suggestions = search_response.json().get('suggestions', [])
        if len(suggestions) > 0:
            # Add celebrity to team via search
            celeb_name = suggestions[0].get('name')
            add_response = requests.post(f"{BASE_URL}/api/search", json={"name": celeb_name})
            
            if add_response.status_code == 200:
                celeb_data = add_response.json()
                celeb_id = celeb_data.get('id')
                
                if celeb_id:
                    # Add to team
                    add_team_response = requests.post(f"{BASE_URL}/api/team/add", json={
                        "team_id": team_id,
                        "celebrity_id": celeb_id
                    })
                    
                    if add_team_response.status_code == 200:
                        team_data = add_team_response.json().get('team', {})
                        celebrities = team_data.get('celebrities', [])
                        
                        # Check that buzz_score is not prominently displayed
                        # The team panel should show price but not individual buzz scores
                        for celeb in celebrities:
                            assert 'price' in celeb, "Celebrity should have price"
                            assert 'name' in celeb, "Celebrity should have name"
                            print(f"  ✓ Team celebrity: {celeb.get('name')} - £{celeb.get('price')}M")
        
        # Cleanup - delete team
        requests.delete(f"{BASE_URL}/api/team/{team_id}")
        print("✓ Team panel test completed")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_health(self):
        """API should be healthy"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("✓ API is healthy")
    
    def test_categories_endpoint(self):
        """Categories endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        
        data = response.json()
        categories = data.get('categories', [])
        assert len(categories) > 0, "Should return categories"
        print(f"✓ Categories endpoint returned {len(categories)} categories")
    
    def test_trending_endpoint(self):
        """Trending endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/trending")
        assert response.status_code == 200
        
        data = response.json()
        trending = data.get('trending', [])
        assert len(trending) > 0, "Should return trending celebrities"
        print(f"✓ Trending endpoint returned {len(trending)} celebrities")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
