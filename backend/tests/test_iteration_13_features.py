"""
Test Iteration 13 Features:
1. Hot Celebs ticker with new celebs (Timothée Chalamet, Zendaya, Travis Kelce, Sydney Sweeney)
2. Category misclassification fixes (Michael Caine, Ian McKellen, Morgan Freeman as movie_stars)
3. Price consistency between Hot Celebs and search
4. How It Works text visibility (text-[10px])
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://media-fame-tracker.preview.emergentagent.com').rstrip('/')


class TestCategoryClassification:
    """Test that actors are correctly classified as movie_stars, not royals or musicians"""
    
    def test_michael_caine_is_movie_star(self):
        """Michael Caine should be classified as movie_stars, not royals"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Michael Caine"},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        celebrity = data.get("celebrity", {})
        
        assert celebrity.get("name") == "Michael Caine", f"Expected Michael Caine, got {celebrity.get('name')}"
        assert celebrity.get("category") == "movie_stars", f"Expected movie_stars, got {celebrity.get('category')}"
        
        print(f"✓ Michael Caine: category={celebrity.get('category')}, tier={celebrity.get('tier')}, price=£{celebrity.get('price')}M")
    
    def test_ian_mckellen_is_movie_star(self):
        """Ian McKellen should be classified as movie_stars, not royals"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Ian McKellen"},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        celebrity = data.get("celebrity", {})
        
        assert celebrity.get("name") == "Ian McKellen", f"Expected Ian McKellen, got {celebrity.get('name')}"
        assert celebrity.get("category") == "movie_stars", f"Expected movie_stars, got {celebrity.get('category')}"
        
        print(f"✓ Ian McKellen: category={celebrity.get('category')}, tier={celebrity.get('tier')}, price=£{celebrity.get('price')}M")
    
    def test_morgan_freeman_is_movie_star(self):
        """Morgan Freeman should be classified as movie_stars, not musicians"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Morgan Freeman"},
            timeout=15
        )
        assert response.status_code == 200
        
        data = response.json()
        celebrity = data.get("celebrity", {})
        
        assert celebrity.get("name") == "Morgan Freeman", f"Expected Morgan Freeman, got {celebrity.get('name')}"
        assert celebrity.get("category") == "movie_stars", f"Expected movie_stars, got {celebrity.get('category')}"
        
        print(f"✓ Morgan Freeman: category={celebrity.get('category')}, tier={celebrity.get('tier')}, price=£{celebrity.get('price')}M")


class TestHotCelebsPool:
    """Test that new celebs are in the Hot Celebs pool"""
    
    def test_hot_celebs_endpoint_works(self):
        """Hot celebs endpoint should return data"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        assert len(hot_celebs) > 0, "Should return at least one hot celeb"
        
        # Check structure of hot celeb
        first_celeb = hot_celebs[0]
        assert "name" in first_celeb, "Hot celeb should have name"
        assert "tier" in first_celeb, "Hot celeb should have tier"
        assert "price" in first_celeb, "Hot celeb should have price"
        assert "hot_reason" in first_celeb, "Hot celeb should have hot_reason"
        assert "image" in first_celeb, "Hot celeb should have image"
        
        print(f"✓ Hot celebs endpoint returns {len(hot_celebs)} celebs")
        for celeb in hot_celebs[:5]:
            print(f"  - {celeb['name']} | Tier: {celeb['tier']} | £{celeb['price']}M | {celeb.get('hot_reason', 'N/A')}")
    
    def test_new_celebs_in_pool(self):
        """New celebs (Timothée Chalamet, Zendaya, Travis Kelce, Sydney Sweeney) should appear in hot celebs"""
        new_celebs = ["Timothée Chalamet", "Zendaya", "Travis Kelce", "Sydney Sweeney"]
        found_celebs = set()
        
        # Make multiple requests since hot celebs are randomized
        for i in range(15):
            response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
            assert response.status_code == 200
            
            data = response.json()
            hot_celebs = data.get("hot_celebs", [])
            
            for celeb in hot_celebs:
                name = celeb.get("name", "")
                for new_celeb in new_celebs:
                    if new_celeb.lower() in name.lower():
                        found_celebs.add(new_celeb)
            
            # If we found all, stop early
            if len(found_celebs) == len(new_celebs):
                break
            
            time.sleep(0.3)
        
        print(f"✓ Found {len(found_celebs)}/{len(new_celebs)} new celebs in hot celebs pool:")
        for celeb in found_celebs:
            print(f"  - {celeb}")
        
        # Should find at least 2 of the 4 new celebs (randomization may not show all)
        assert len(found_celebs) >= 2, f"Expected at least 2 new celebs, found {len(found_celebs)}: {found_celebs}"


class TestPriceConsistency:
    """Test that prices are consistent between Hot Celebs and search"""
    
    def test_price_consistency_for_hot_celeb(self):
        """Price in Hot Celebs should match price when searching for the same celeb"""
        # Get a hot celeb
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        if not hot_celebs:
            pytest.skip("No hot celebs available")
        
        # Pick first hot celeb
        hot_celeb = hot_celebs[0]
        hot_name = hot_celeb.get("name")
        hot_price = hot_celeb.get("price")
        hot_tier = hot_celeb.get("tier")
        
        print(f"Hot Celeb: {hot_name} | Tier: {hot_tier} | Price: £{hot_price}M")
        
        # Search for the same celeb
        search_response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": hot_name},
            timeout=15
        )
        assert search_response.status_code == 200
        
        search_data = search_response.json()
        search_celeb = search_data.get("celebrity", {})
        search_price = search_celeb.get("price")
        search_tier = search_celeb.get("tier")
        
        print(f"Search Result: {search_celeb.get('name')} | Tier: {search_tier} | Price: £{search_price}M")
        
        # Prices should match (or be very close due to dynamic pricing)
        price_diff = abs(hot_price - search_price)
        assert price_diff <= 1.0, f"Price mismatch: Hot Celebs £{hot_price}M vs Search £{search_price}M (diff: £{price_diff}M)"
        
        print(f"✓ Price consistency verified: Hot Celebs £{hot_price}M ≈ Search £{search_price}M")


class TestHotCelebsStructure:
    """Test the structure and content of Hot Celebs data"""
    
    def test_hot_celeb_has_hot_reason(self):
        """Each hot celeb should have a hot_reason explaining why they're trending"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        for celeb in hot_celebs:
            assert "hot_reason" in celeb, f"Hot celeb {celeb.get('name')} missing hot_reason"
            assert len(celeb.get("hot_reason", "")) > 0, f"Hot celeb {celeb.get('name')} has empty hot_reason"
            print(f"✓ {celeb.get('name')}: {celeb.get('hot_reason')}")
    
    def test_hot_celeb_has_image(self):
        """Each hot celeb should have an image URL"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        for celeb in hot_celebs:
            assert "image" in celeb, f"Hot celeb {celeb.get('name')} missing image"
            assert len(celeb.get("image", "")) > 0, f"Hot celeb {celeb.get('name')} has empty image"
            # Image should be a valid URL
            image_url = celeb.get("image", "")
            assert image_url.startswith("http"), f"Hot celeb {celeb.get('name')} has invalid image URL: {image_url}"
        
        print(f"✓ All {len(hot_celebs)} hot celebs have valid image URLs")
    
    def test_hot_celeb_tier_and_price_valid(self):
        """Each hot celeb should have valid tier (A/B/C/D) and price within tier range"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        hot_celebs = data.get("hot_celebs", [])
        
        tier_price_ranges = {
            "A": (9.0, 12.0),
            "B": (5.0, 8.0),
            "C": (2.0, 4.0),
            "D": (0.5, 1.5)
        }
        
        for celeb in hot_celebs:
            tier = celeb.get("tier")
            price = celeb.get("price")
            
            assert tier in ["A", "B", "C", "D"], f"Invalid tier {tier} for {celeb.get('name')}"
            
            min_price, max_price = tier_price_ranges[tier]
            assert min_price <= price <= max_price, f"Price £{price}M out of range for {tier}-LIST ({min_price}-{max_price}) for {celeb.get('name')}"
            
            print(f"✓ {celeb.get('name')}: {tier}-LIST £{price}M (valid range: £{min_price}-{max_price}M)")


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """API root should return version info"""
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data, "Should have message"
        assert "version" in data, "Should have version"
        print(f"✓ API: {data.get('message')} v{data.get('version')}")
    
    def test_categories_endpoint(self):
        """Categories endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/categories", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data, "Should have categories array"
        
        # Verify movie_stars category exists
        categories = data.get("categories", [])
        category_ids = [c.get("id") for c in categories]
        assert "movie_stars" in category_ids, "movie_stars category should exist"
        
        print(f"✓ Categories: {category_ids}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
