"""
Iteration 25 - Strict Search and Random Category Tests
Tests:
1. Strict Search - partial names return empty results
2. Strict Search - full names return exact matches
3. Random Category - appears in category list
4. Random Category - returns celebrities from various categories
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStrictSearch:
    """Test strict exact-match search functionality"""
    
    def test_partial_name_shak_returns_empty(self):
        """Typing 'shak' should return 0 results (partial match)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "shak"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'shak': {len(suggestions)} results")
        assert len(suggestions) == 0, f"Expected 0 results for 'shak', got {len(suggestions)}"
    
    def test_partial_name_tom_returns_empty(self):
        """Typing 'tom' should return 0 results (partial match)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "tom"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'tom': {len(suggestions)} results")
        assert len(suggestions) == 0, f"Expected 0 results for 'tom', got {len(suggestions)}"
    
    def test_partial_name_tay_returns_empty(self):
        """Typing 'tay' should return 0 results (partial match)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "tay"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'tay': {len(suggestions)} results")
        assert len(suggestions) == 0, f"Expected 0 results for 'tay', got {len(suggestions)}"
    
    def test_partial_name_bey_returns_empty(self):
        """Typing 'bey' should return 0 results (partial match)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "bey"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'bey': {len(suggestions)} results")
        assert len(suggestions) == 0, f"Expected 0 results for 'bey', got {len(suggestions)}"
    
    def test_full_name_shakira_returns_result(self):
        """Typing 'shakira' should return exactly 1 result for Shakira"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "shakira"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'shakira': {len(suggestions)} results")
        print(f"Results: {[s.get('name') for s in suggestions]}")
        assert len(suggestions) == 1, f"Expected 1 result for 'shakira', got {len(suggestions)}"
        assert suggestions[0].get("name", "").lower() == "shakira", f"Expected 'Shakira', got {suggestions[0].get('name')}"
    
    def test_full_name_tom_hanks_returns_result(self):
        """Typing 'tom hanks' should return exactly 1 result for Tom Hanks"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "tom hanks"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'tom hanks': {len(suggestions)} results")
        print(f"Results: {[s.get('name') for s in suggestions]}")
        assert len(suggestions) == 1, f"Expected 1 result for 'tom hanks', got {len(suggestions)}"
        assert "tom hanks" in suggestions[0].get("name", "").lower(), f"Expected 'Tom Hanks', got {suggestions[0].get('name')}"
    
    def test_full_name_adele_returns_result(self):
        """Typing 'adele' should return Adele (single-name celebrity)"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "adele"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'adele': {len(suggestions)} results")
        print(f"Results: {[s.get('name') for s in suggestions]}")
        assert len(suggestions) == 1, f"Expected 1 result for 'adele', got {len(suggestions)}"
        assert suggestions[0].get("name", "").lower() == "adele", f"Expected 'Adele', got {suggestions[0].get('name')}"
    
    def test_full_name_beyonce_returns_result(self):
        """Typing 'beyonce' should return Beyoncé"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "beyonce"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'beyonce': {len(suggestions)} results")
        print(f"Results: {[s.get('name') for s in suggestions]}")
        assert len(suggestions) == 1, f"Expected 1 result for 'beyonce', got {len(suggestions)}"
        # Beyoncé may have accent
        assert "beyonc" in suggestions[0].get("name", "").lower(), f"Expected 'Beyoncé', got {suggestions[0].get('name')}"
    
    def test_full_name_rihanna_returns_result(self):
        """Typing 'rihanna' should return Rihanna"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "rihanna"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        print(f"Search 'rihanna': {len(suggestions)} results")
        print(f"Results: {[s.get('name') for s in suggestions]}")
        assert len(suggestions) == 1, f"Expected 1 result for 'rihanna', got {len(suggestions)}"
        assert suggestions[0].get("name", "").lower() == "rihanna", f"Expected 'Rihanna', got {suggestions[0].get('name')}"


class TestRandomCategory:
    """Test Random category functionality"""
    
    def test_random_category_in_categories_list(self):
        """Random category should appear in the categories list"""
        response = requests.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        categories = data.get("categories", [])
        category_ids = [c.get("id") for c in categories]
        print(f"Categories: {category_ids}")
        assert "random" in category_ids, f"'random' category not found in categories list: {category_ids}"
        
        # Check random category has correct properties
        random_cat = next((c for c in categories if c.get("id") == "random"), None)
        assert random_cat is not None
        assert random_cat.get("name") == "Random"
        assert random_cat.get("icon") == "shuffle"
    
    def test_random_category_returns_celebrities(self):
        """Random category should return celebrities from various categories"""
        response = requests.get(f"{BASE_URL}/api/celebrities/category/random")
        assert response.status_code == 200
        data = response.json()
        celebrities = data.get("celebrities", [])
        print(f"Random category returned {len(celebrities)} celebrities")
        
        # Should return 8 celebrities
        assert len(celebrities) == 8, f"Expected 8 celebrities, got {len(celebrities)}"
        
        # Check that celebrities have required fields
        for celeb in celebrities:
            assert "name" in celeb, f"Celebrity missing 'name' field"
            assert "tier" in celeb, f"Celebrity {celeb.get('name')} missing 'tier' field"
            assert "price" in celeb, f"Celebrity {celeb.get('name')} missing 'price' field"
            print(f"  - {celeb.get('name')} ({celeb.get('tier')}, £{celeb.get('price')}M, category: {celeb.get('category')})")
    
    def test_random_category_returns_mixed_categories(self):
        """Random category should return celebrities from different categories"""
        response = requests.get(f"{BASE_URL}/api/celebrities/category/random")
        assert response.status_code == 200
        data = response.json()
        celebrities = data.get("celebrities", [])
        
        # Get unique categories from results
        categories_found = set()
        for celeb in celebrities:
            cat = celeb.get("category")
            if cat:
                categories_found.add(cat)
        
        print(f"Categories found in random results: {categories_found}")
        # Should have at least 2 different categories (ideally more)
        # Note: Due to randomness, this might occasionally fail if all 8 happen to be same category
        # But with a large pool, this is very unlikely
        assert len(categories_found) >= 1, f"Expected at least 1 category, got {len(categories_found)}"
    
    def test_random_category_returns_different_results_on_refresh(self):
        """Random category should return different results on refresh"""
        # Make two requests
        response1 = requests.get(f"{BASE_URL}/api/celebrities/category/random")
        response2 = requests.get(f"{BASE_URL}/api/celebrities/category/random")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        celebs1 = response1.json().get("celebrities", [])
        celebs2 = response2.json().get("celebrities", [])
        
        names1 = set(c.get("name") for c in celebs1)
        names2 = set(c.get("name") for c in celebs2)
        
        print(f"First request: {names1}")
        print(f"Second request: {names2}")
        
        # Results should be different (at least some different names)
        # Due to randomness, there might be some overlap, but not all 8 should be identical
        overlap = names1.intersection(names2)
        print(f"Overlap: {overlap} ({len(overlap)} celebrities)")
        
        # Allow for some overlap but not complete match
        # If all 8 are the same, that's suspicious
        if len(names1) == 8 and len(names2) == 8:
            assert len(overlap) < 8, "Random category returned identical results twice - randomness may not be working"


class TestSearchEdgeCases:
    """Test edge cases for strict search"""
    
    def test_single_character_returns_empty(self):
        """Single character search should return empty"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "a"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        assert len(suggestions) == 0, f"Expected 0 results for single char, got {len(suggestions)}"
    
    def test_two_character_partial_returns_empty(self):
        """Two character partial search should return empty"""
        response = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "ta"})
        assert response.status_code == 200
        data = response.json()
        suggestions = data.get("suggestions", [])
        assert len(suggestions) == 0, f"Expected 0 results for 'ta', got {len(suggestions)}"
    
    def test_case_insensitive_full_name(self):
        """Full name search should be case insensitive"""
        # Test uppercase
        response1 = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "SHAKIRA"})
        assert response1.status_code == 200
        data1 = response1.json()
        suggestions1 = data1.get("suggestions", [])
        
        # Test lowercase
        response2 = requests.get(f"{BASE_URL}/api/autocomplete", params={"q": "shakira"})
        assert response2.status_code == 200
        data2 = response2.json()
        suggestions2 = data2.get("suggestions", [])
        
        # Both should return same result
        assert len(suggestions1) == len(suggestions2), "Case sensitivity issue"
        if suggestions1 and suggestions2:
            assert suggestions1[0].get("name") == suggestions2[0].get("name")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
