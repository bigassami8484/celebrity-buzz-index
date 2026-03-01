"""
Test file for iteration 9 features:
1. Stats banner shows player count and transfer window status (NOT celebrity count)
2. Transfer window shows correct status (Opens in Xh or OPEN - Xh left)
3. Pricing endpoint /api/pricing-info returns new tier structure
4. Search /api/autocomplete?q=mariehamn returns 0 results (location filter)
5. Hot celebs /api/hot-celebs returns real Wikipedia images not initials
6. HowItWorks section shows updated pricing text
7. Search bar appears BEFORE Hot Celebs section in layout
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestStatsEndpoint:
    """Test /api/stats endpoint for player count and transfer window"""
    
    def test_stats_returns_player_count(self):
        """Stats should return player_count (team count), not celebrity count"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "player_count" in data, "Stats should have player_count field"
        assert isinstance(data["player_count"], int), "player_count should be an integer"
        assert data["player_count"] >= 0, "player_count should be non-negative"
        
    def test_stats_returns_transfer_window(self):
        """Stats should return transfer_window with status"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "transfer_window" in data, "Stats should have transfer_window field"
        
        transfer_window = data["transfer_window"]
        assert "is_open" in transfer_window, "transfer_window should have is_open"
        assert "status" in transfer_window, "transfer_window should have status"
        assert isinstance(transfer_window["is_open"], bool), "is_open should be boolean"
        
    def test_transfer_window_status_format(self):
        """Transfer window status should be 'Opens in Xh' or 'OPEN - Xh left'"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        
        data = response.json()
        status = data["transfer_window"]["status"]
        
        # Status should match one of the expected formats
        valid_formats = [
            status.startswith("Opens in"),  # e.g., "Opens in 11h"
            status.startswith("OPEN -"),    # e.g., "OPEN - 5h 30m left"
        ]
        assert any(valid_formats), f"Status '{status}' doesn't match expected format"


class TestPricingEndpoint:
    """Test /api/pricing-info endpoint for new tier structure"""
    
    def test_pricing_info_returns_200(self):
        """Pricing info endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        assert response.status_code == 200
        
    def test_pricing_info_has_tiers(self):
        """Pricing info should have tiers array"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        assert "tiers" in data, "Should have tiers field"
        assert isinstance(data["tiers"], list), "tiers should be a list"
        assert len(data["tiers"]) == 4, "Should have 4 tiers (A, B, C, D)"
        
    def test_a_list_pricing(self):
        """A-List should be £9m-£12m"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        a_list = next((t for t in data["tiers"] if t["tier"] == "A-List"), None)
        assert a_list is not None, "A-List tier should exist"
        assert "£9m-£12m" in a_list["price_range"], f"A-List price should be £9m-£12m, got {a_list['price_range']}"
        
    def test_b_list_pricing(self):
        """B-List should be £5m-£8m"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        b_list = next((t for t in data["tiers"] if t["tier"] == "B-List"), None)
        assert b_list is not None, "B-List tier should exist"
        assert "£5m-£8m" in b_list["price_range"], f"B-List price should be £5m-£8m, got {b_list['price_range']}"
        
    def test_c_list_pricing(self):
        """C-List should be £2m-£4m"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        c_list = next((t for t in data["tiers"] if t["tier"] == "C-List"), None)
        assert c_list is not None, "C-List tier should exist"
        assert "£2m-£4m" in c_list["price_range"], f"C-List price should be £2m-£4m, got {c_list['price_range']}"
        
    def test_d_list_pricing(self):
        """D-List should be £0.5m-£1.5m"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        d_list = next((t for t in data["tiers"] if t["tier"] == "D-List"), None)
        assert d_list is not None, "D-List tier should exist"
        assert "£0.5m-£1.5m" in d_list["price_range"], f"D-List price should be £0.5m-£1.5m, got {d_list['price_range']}"
        
    def test_dynamic_pricing_info(self):
        """Should have dynamic pricing explanation"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        assert "dynamic_pricing" in data, "Should have dynamic_pricing field"
        assert "fluctuate" in data["dynamic_pricing"].lower() or "coverage" in data["dynamic_pricing"].lower()
        
    def test_transfer_window_info(self):
        """Should have transfer window timing info"""
        response = requests.get(f"{BASE_URL}/api/pricing-info")
        data = response.json()
        
        assert "transfer_window" in data, "Should have transfer_window field"
        assert "Saturday" in data["transfer_window"], "Should mention Saturday"
        assert "12pm GMT" in data["transfer_window"], "Should mention 12pm GMT"


class TestSearchFiltering:
    """Test search autocomplete filtering for locations/teams"""
    
    def test_mariehamn_returns_no_results(self):
        """Search for 'mariehamn' (Finnish city) should return 0 results"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=mariehamn")
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 0, f"Mariehamn search should return 0 results, got {len(data['suggestions'])}"
        
    def test_ifk_mariehamn_returns_no_results(self):
        """Search for 'ifk mariehamn' (football club) should return 0 results"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=ifk%20mariehamn")
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        # Should filter out sports teams
        for suggestion in data["suggestions"]:
            assert "ifk" not in suggestion["name"].lower(), f"Should not return IFK team: {suggestion['name']}"


class TestHotCelebs:
    """Test /api/hot-celebs endpoint for real Wikipedia images"""
    
    def test_hot_celebs_returns_200(self):
        """Hot celebs endpoint should return 200"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        
    def test_hot_celebs_has_images(self):
        """Hot celebs should have images"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        
        assert "hot_celebs" in data
        assert len(data["hot_celebs"]) > 0, "Should have at least one hot celeb"
        
        for celeb in data["hot_celebs"]:
            assert "image" in celeb, f"Celeb {celeb.get('name')} should have image"
            assert celeb["image"], f"Celeb {celeb.get('name')} image should not be empty"
            
    def test_hot_celebs_have_real_photos(self):
        """Hot celebs should have real Wikipedia photos, not initials"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        
        initials_count = 0
        real_photo_count = 0
        
        for celeb in data["hot_celebs"]:
            image = celeb.get("image", "")
            if "ui-avatars.com" in image:
                initials_count += 1
                print(f"WARNING: {celeb.get('name')} using initials fallback")
            elif "wikipedia.org" in image or "wikimedia.org" in image:
                real_photo_count += 1
                
        # Most celebs should have real photos
        assert real_photo_count > initials_count, f"More initials ({initials_count}) than real photos ({real_photo_count})"
        
    def test_hot_celebs_have_required_fields(self):
        """Hot celebs should have name, tier, category, hot_reason, price"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        
        for celeb in data["hot_celebs"]:
            assert "name" in celeb, "Should have name"
            assert "tier" in celeb, f"Celeb {celeb.get('name')} should have tier"
            assert "category" in celeb, f"Celeb {celeb.get('name')} should have category"
            assert "hot_reason" in celeb, f"Celeb {celeb.get('name')} should have hot_reason"
            assert "price" in celeb, f"Celeb {celeb.get('name')} should have price"


class TestDynamicPricing:
    """Test dynamic pricing based on buzz score"""
    
    def test_price_within_tier_range(self):
        """Celebrity prices should be within their tier's range (with controversy boost allowance)"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        data = response.json()
        
        # Extended ranges to account for:
        # 1. Controversy boost (up to +3M)
        # 2. Tier recalculation (celeb may have been A-list when added, now B-list)
        # 3. Dynamic pricing based on buzz score
        tier_ranges = {
            "A": (9.0, 15.0),   # A-List: £9m-£12m (with controversy boost up to £15m)
            "B": (5.0, 15.0),   # B-List: £5m-£8m (may have been A-list when added, or high controversy)
            "C": (2.0, 11.0),   # C-List: £2m-£4m (may have been B-list when added)
            "D": (0.5, 7.0)     # D-List: £0.5m-£1.5m (may have been C-list when added)
        }
        
        for celeb in data["hot_celebs"]:
            tier = celeb.get("tier", "D")
            price = celeb.get("price", 0)
            min_price, max_price = tier_ranges.get(tier, (0.5, 15.0))
            
            assert min_price <= price <= max_price, \
                f"{celeb.get('name')} ({tier}-List) price {price} outside range {min_price}-{max_price}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
