"""
Test iteration 15 - UI/UX changes verification
Tests:
1. Hot Celebs banner auto-scroll (API returns data)
2. News API endpoint with 24-hour caching
3. Basic app functionality (search, categories)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHotCelebsBanner:
    """Test Hot Celebs banner functionality"""
    
    def test_hot_celebs_endpoint_returns_data(self):
        """Verify /api/hot-celebs returns celebrity data"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "hot_celebs" in data
        assert len(data["hot_celebs"]) > 0
        
        # Verify each celeb has required fields
        for celeb in data["hot_celebs"]:
            assert "name" in celeb
            assert "tier" in celeb
            assert "price" in celeb
            assert "image" in celeb
            assert "hot_reason" in celeb
            
        print(f"✓ Hot Celebs endpoint returned {len(data['hot_celebs'])} celebrities")
    
    def test_hot_celebs_prices_within_tier_ranges(self):
        """Verify prices are within correct tier ranges"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        tier_ranges = {
            "A": (9.0, 12.0),
            "B": (5.0, 8.0),
            "C": (2.0, 4.0),
            "D": (0.5, 1.5)
        }
        
        for celeb in data["hot_celebs"]:
            tier = celeb.get("tier", "D")
            price = celeb.get("price", 0)
            min_price, max_price = tier_ranges.get(tier, (0.5, 1.5))
            
            assert min_price <= price <= max_price, \
                f"{celeb['name']} ({tier}-list) price £{price}M outside range £{min_price}-{max_price}M"
        
        print("✓ All Hot Celebs prices within correct tier ranges")


class TestTodaysNewsAPI:
    """Test Today's News API with 24-hour caching"""
    
    def test_todays_news_endpoint_returns_data(self):
        """Verify /api/todays-news returns news data"""
        response = requests.get(f"{BASE_URL}/api/todays-news", timeout=15)
        assert response.status_code == 200
        
        data = response.json()
        assert "news" in data
        assert len(data["news"]) > 0
        
        # Verify each news item has required fields
        for item in data["news"]:
            assert "headline" in item
            assert "source" in item
            assert "url" in item
            
        print(f"✓ Today's News endpoint returned {len(data['news'])} news items")
    
    def test_news_caching_returns_same_data(self):
        """Verify news is cached (same data on subsequent requests)"""
        # First request
        response1 = requests.get(f"{BASE_URL}/api/todays-news", timeout=15)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Wait a moment
        time.sleep(1)
        
        # Second request should return cached data
        response2 = requests.get(f"{BASE_URL}/api/todays-news", timeout=15)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Headlines should be the same (cached)
        headlines1 = [item.get("headline") for item in data1.get("news", [])]
        headlines2 = [item.get("headline") for item in data2.get("news", [])]
        
        assert headlines1 == headlines2, "News should be cached and return same data"
        print("✓ News caching working - same data returned on subsequent requests")


class TestBasicAppFunctionality:
    """Test basic app functionality still works"""
    
    def test_categories_endpoint(self):
        """Verify /api/categories returns category data"""
        response = requests.get(f"{BASE_URL}/api/categories", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
        
        expected_categories = ["movie_stars", "tv_actors", "musicians", "athletes", "royals", "reality_tv", "other"]
        category_ids = [cat.get("id") for cat in data["categories"]]
        
        for expected in expected_categories:
            assert expected in category_ids, f"Missing category: {expected}"
        
        print(f"✓ Categories endpoint returned {len(data['categories'])} categories")
    
    def test_search_celebrity(self):
        """Verify celebrity search works"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Tom Hanks"},
            timeout=30
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "celebrity" in data
        assert data["celebrity"].get("name") is not None
        
        print(f"✓ Celebrity search returned: {data['celebrity'].get('name')}")
    
    def test_stats_endpoint(self):
        """Verify /api/stats returns player count and transfer window"""
        response = requests.get(f"{BASE_URL}/api/stats", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "player_count" in data
        assert "transfer_window" in data
        assert "is_open" in data["transfer_window"]
        assert "status" in data["transfer_window"]
        
        print(f"✓ Stats endpoint returned player_count: {data['player_count']}")


class TestPricingInfo:
    """Test pricing info endpoint"""
    
    def test_pricing_info_endpoint(self):
        """Verify /api/pricing-info returns tier information"""
        response = requests.get(f"{BASE_URL}/api/pricing-info", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        assert "tiers" in data
        assert len(data["tiers"]) == 4  # A, B, C, D
        
        # Verify tier ranges
        tier_info = {tier["tier"]: tier["price_range"] for tier in data["tiers"]}
        assert "A-List" in tier_info
        assert "B-List" in tier_info
        assert "C-List" in tier_info
        assert "D-List" in tier_info
        
        print("✓ Pricing info endpoint returned all tier information")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
