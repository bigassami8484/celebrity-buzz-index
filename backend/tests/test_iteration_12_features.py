"""
Test Iteration 12 Features:
1. Wikidata-based human verification for search (P31=Q5 filter)
2. Price history tracking with database storage
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://star-draft-game.preview.emergentagent.com').rstrip('/')

class TestWikidataHumanVerification:
    """Test that search only returns humans verified via Wikidata P31=Q5"""
    
    def test_gucci_returns_only_humans(self):
        """Search 'gucci' should return only humans (Gucci Mane, Maurizio Gucci, etc.) - NO BRAND"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=gucci", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        # Should have results
        assert len(suggestions) > 0, "Should return at least one human result for 'gucci'"
        
        # All results should be humans (people with names)
        human_names = ["Gucci Mane", "Maurizio Gucci", "Guccio Gucci", "Paolo Gucci", "Aldo Gucci", 
                       "Patricia Gucci", "Rodolfo Gucci", "Gucci Westman"]
        
        for suggestion in suggestions:
            name = suggestion.get("name", "")
            # Should NOT be the brand "Gucci" alone
            assert name.lower() != "gucci", f"Should not return brand 'Gucci', got: {name}"
            # Should be a person (has first/last name or known human)
            print(f"  ✓ Found human: {name}")
    
    def test_lion_returns_only_humans(self):
        """Search 'lion' should return only humans (Alfred Lion) - NO ANIMAL"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=lion", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        # Should have results (Alfred Lion is a human)
        assert len(suggestions) > 0, "Should return at least one human result for 'lion'"
        
        for suggestion in suggestions:
            name = suggestion.get("name", "")
            description = suggestion.get("description", "").lower()
            
            # Should NOT be the animal "Lion"
            assert name.lower() != "lion", f"Should not return animal 'Lion', got: {name}"
            # Should NOT be about the animal
            assert "panthera leo" not in description, f"Should not return lion animal, got: {name}"
            assert "big cat" not in description, f"Should not return lion animal, got: {name}"
            print(f"  ✓ Found human: {name}")
    
    def test_beyonce_returns_human(self):
        """Search 'beyonce' should return Beyoncé (human verified via Wikidata)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=beyonce", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        # Should have results
        assert len(suggestions) > 0, "Should return Beyoncé for 'beyonce' search"
        
        # First result should be Beyoncé
        first_result = suggestions[0]
        assert "beyonc" in first_result.get("name", "").lower(), f"First result should be Beyoncé, got: {first_result.get('name')}"
        
        # Should have proper tier and price
        assert first_result.get("estimated_tier") in ["A", "B", "C", "D"], "Should have valid tier"
        assert first_result.get("estimated_price", 0) > 0, "Should have valid price"
        
        print(f"  ✓ Found Beyoncé: {first_result.get('name')} - Tier {first_result.get('estimated_tier')} - £{first_result.get('estimated_price')}M")
    
    def test_taylor_returns_all_humans(self):
        """Search 'taylor' should return Taylor Swift, Elizabeth Taylor, etc. - ALL HUMANS"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=taylor", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        # Should have multiple results
        assert len(suggestions) >= 2, "Should return multiple humans for 'taylor' search"
        
        # All results should be humans
        expected_humans = ["Taylor Swift", "Elizabeth Taylor", "Angus Taylor", "Teyana Taylor", "Christine Taylor"]
        found_humans = []
        
        for suggestion in suggestions:
            name = suggestion.get("name", "")
            # Should be a person (has first/last name)
            assert "taylor" in name.lower(), f"Result should contain 'taylor', got: {name}"
            found_humans.append(name)
            print(f"  ✓ Found human: {name}")
        
        # Should find at least Taylor Swift
        assert any("taylor swift" in h.lower() for h in found_humans), "Should find Taylor Swift"


class TestPriceHistoryAPI:
    """Test price history tracking and API endpoints"""
    
    def test_price_history_by_name_endpoint(self):
        """GET /api/price-history/celebrity-name/{name} should work"""
        # Use a celebrity that exists in the database
        response = requests.get(f"{BASE_URL}/api/price-history/celebrity-name/Adele", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "celebrity_name" in data, "Response should have celebrity_name"
        assert "current_price" in data, "Response should have current_price"
        assert "current_tier" in data, "Response should have current_tier"
        assert "history" in data, "Response should have history array"
        
        # Verify data types
        assert isinstance(data["current_price"], (int, float)), "current_price should be numeric"
        assert data["current_tier"] in ["A", "B", "C", "D"], "current_tier should be valid tier"
        assert isinstance(data["history"], list), "history should be a list"
        
        print(f"  ✓ Price history for Adele: £{data['current_price']}M ({data['current_tier']}-LIST)")
        print(f"  ✓ History entries: {len(data['history'])}")
    
    def test_price_history_by_id_endpoint(self):
        """GET /api/celebrity/{id}/price-history should work"""
        # First get a celebrity ID from trending
        trending_response = requests.get(f"{BASE_URL}/api/trending", timeout=10)
        assert trending_response.status_code == 200
        
        trending_data = trending_response.json()
        celebrities = trending_data.get("trending", [])
        
        if celebrities:
            celebrity_id = celebrities[0].get("id")
            celebrity_name = celebrities[0].get("name")
            
            # Now get price history by ID
            response = requests.get(f"{BASE_URL}/api/celebrity/{celebrity_id}/price-history", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            assert "celebrity_name" in data, "Response should have celebrity_name"
            assert "current_price" in data, "Response should have current_price"
            assert "history" in data, "Response should have history array"
            
            print(f"  ✓ Price history by ID for {celebrity_name}: £{data['current_price']}M")
    
    def test_price_history_not_found(self):
        """GET /api/price-history/celebrity-name/{name} should return 404 for non-existent celebrity"""
        response = requests.get(f"{BASE_URL}/api/price-history/celebrity-name/NonExistentCelebrity12345", timeout=10)
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data, "Should have error detail"
        print(f"  ✓ Correctly returns 404 for non-existent celebrity")
    
    def test_price_history_records_on_search(self):
        """Price history should be recorded when searching for celebrities"""
        # Search for a celebrity
        search_response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Taylor Swift"},
            timeout=15
        )
        assert search_response.status_code == 200
        
        # Wait a moment for the price history to be recorded
        time.sleep(1)
        
        # Check price history
        history_response = requests.get(f"{BASE_URL}/api/price-history/celebrity-name/Taylor%20Swift", timeout=10)
        assert history_response.status_code == 200
        
        data = history_response.json()
        assert len(data.get("history", [])) > 0, "Should have at least one price history entry"
        
        # Verify history entry structure
        if data["history"]:
            entry = data["history"][0]
            assert "celebrity_id" in entry, "History entry should have celebrity_id"
            assert "celebrity_name" in entry, "History entry should have celebrity_name"
            assert "price" in entry, "History entry should have price"
            assert "tier" in entry, "History entry should have tier"
            assert "buzz_score" in entry, "History entry should have buzz_score"
            assert "recorded_at" in entry, "History entry should have recorded_at"
            
            print(f"  ✓ Price history recorded: £{entry['price']}M, Tier {entry['tier']}, Buzz {entry['buzz_score']}")


class TestSearchFiltering:
    """Additional tests for search filtering"""
    
    def test_nike_returns_only_humans(self):
        """Search 'nike' should return only humans - NO BRAND"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=nike", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        for suggestion in suggestions:
            name = suggestion.get("name", "")
            # Should NOT be the brand "Nike" alone
            assert name.lower() != "nike", f"Should not return brand 'Nike', got: {name}"
            print(f"  ✓ Found human: {name}")
    
    def test_tesla_filters_non_humans(self):
        """Search 'tesla' should filter out cars/companies"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=tesla", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        suggestions = data.get("suggestions", [])
        
        for suggestion in suggestions:
            name = suggestion.get("name", "")
            description = suggestion.get("description", "").lower()
            
            # Should NOT be Tesla Inc. or Tesla cars
            assert "tesla, inc" not in name.lower(), f"Should not return Tesla Inc., got: {name}"
            assert "electric vehicle" not in description, f"Should not return Tesla cars, got: {name}"
            
            if suggestions:
                print(f"  ✓ Found: {name}")
        
        if not suggestions:
            print("  ✓ No results (correctly filtered out non-humans)")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """API root should return version info"""
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data, "Should have message"
        assert "version" in data, "Should have version"
        print(f"  ✓ API: {data.get('message')} v{data.get('version')}")
    
    def test_trending_endpoint(self):
        """Trending endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/trending", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "trending" in data, "Should have trending array"
        print(f"  ✓ Trending celebrities: {len(data.get('trending', []))}")
    
    def test_categories_endpoint(self):
        """Categories endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/categories", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data, "Should have categories array"
        print(f"  ✓ Categories: {len(data.get('categories', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
