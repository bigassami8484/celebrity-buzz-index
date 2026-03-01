"""
Iteration 22 - Tier/Price Consistency Tests
Tests the fix for tier/price mismatch issue where celebrities showed incorrect tiers and prices.

Key test cases:
1. Daniel Radcliffe - A-list (60+ languages), ~£12M
2. Rochelle Humes - C-list (10-24 languages), ~£2.5M  
3. Pink (singer) - A-list (60+ languages), ~£12M
4. Pink alias mapping - searching 'pink' should return Pink (singer) with correct wiki link
5. Hot celebs banner - all celebrities should have consistent tier/price
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Tier/Price mapping according to the system:
# A-LIST (60+ languages) = £12M base
# B-LIST (25-59 languages) = £6M base
# C-LIST (10-24 languages) = £2.5M base
# D-LIST (<10 languages) = £1M base

TIER_PRICE_MAP = {
    "A": 12.0,
    "B": 6.0,
    "C": 2.5,
    "D": 1.0
}


class TestAPIHealth:
    """Basic API health checks"""
    
    def test_api_root(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestAutocompleteEndpoint:
    """Test autocomplete endpoint tier/price consistency"""
    
    def test_daniel_radcliffe_tier_price(self):
        """Daniel Radcliffe should be A-list with ~£12M price"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Daniel%20Radcliffe")
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        assert len(suggestions) > 0, "Should return at least one suggestion"
        
        # Find Daniel Radcliffe in results
        daniel = None
        for s in suggestions:
            if "daniel radcliffe" in s.get("name", "").lower():
                daniel = s
                break
        
        assert daniel is not None, "Daniel Radcliffe should be in results"
        
        # Verify tier is A (Harry Potter franchise lead, 60+ languages)
        tier = daniel.get("tier") or daniel.get("estimated_tier")
        assert tier == "A", f"Daniel Radcliffe should be A-list, got {tier}"
        
        # Verify price is around £12M (A-list base price)
        price = daniel.get("price") or daniel.get("estimated_price")
        assert price >= 12.0, f"Daniel Radcliffe price should be >= £12M, got £{price}M"
        assert price <= 15.0, f"Daniel Radcliffe price should be <= £15M, got £{price}M"
    
    def test_rochelle_humes_tier_price(self):
        """Rochelle Humes should be C-list with ~£2.5M price"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=Rochelle%20Humes")
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        assert len(suggestions) > 0, "Should return at least one suggestion"
        
        rochelle = suggestions[0]
        
        # Verify tier is C (TV presenter, 10-24 languages)
        tier = rochelle.get("tier") or rochelle.get("estimated_tier")
        assert tier == "C", f"Rochelle Humes should be C-list, got {tier}"
        
        # Verify price is around £2.5M (C-list base price)
        price = rochelle.get("price") or rochelle.get("estimated_price")
        assert price >= 2.0, f"Rochelle Humes price should be >= £2M, got £{price}M"
        assert price <= 4.0, f"Rochelle Humes price should be <= £4M, got £{price}M"
    
    def test_pink_alias_returns_singer(self):
        """Searching 'pink' should return Pink (singer) in results"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=pink")
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        assert len(suggestions) > 0, "Should return at least one suggestion"
        
        # Find Pink (singer) in results
        pink_singer = None
        for s in suggestions:
            if "pink (singer)" in s.get("name", "").lower():
                pink_singer = s
                break
        
        assert pink_singer is not None, "Pink (singer) should be in results when searching 'pink'"
        
        # Verify tier is A (major international artist, 60+ languages)
        tier = pink_singer.get("tier") or pink_singer.get("estimated_tier")
        assert tier == "A", f"Pink (singer) should be A-list, got {tier}"
        
        # Verify price is around £12M (A-list base price)
        price = pink_singer.get("price") or pink_singer.get("estimated_price")
        assert price >= 12.0, f"Pink (singer) price should be >= £12M, got £{price}M"
    
    def test_tier_price_consistency(self):
        """Verify tier and price are consistent for all autocomplete results"""
        test_queries = ["Taylor Swift", "Ed Sheeran", "Tom Holland", "Adele"]
        
        for query in test_queries:
            response = requests.get(f"{BASE_URL}/api/autocomplete?q={query}")
            assert response.status_code == 200
            data = response.json()
            
            suggestions = data.get("suggestions", [])
            for s in suggestions:
                tier = s.get("tier") or s.get("estimated_tier")
                price = s.get("price") or s.get("estimated_price")
                
                if tier and price:
                    expected_base = TIER_PRICE_MAP.get(tier, 2.5)
                    # Price should be within reasonable range of base price (base to base + 50% for premiums)
                    assert price >= expected_base * 0.9, f"{s.get('name')}: Price £{price}M too low for tier {tier} (expected >= £{expected_base * 0.9}M)"
                    assert price <= expected_base * 1.5, f"{s.get('name')}: Price £{price}M too high for tier {tier} (expected <= £{expected_base * 1.5}M)"


class TestCelebritySearchEndpoint:
    """Test celebrity/search endpoint tier/price consistency"""
    
    def test_pink_singer_search(self):
        """POST /api/celebrity/search for Pink (singer) should return correct tier/price"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Pink (singer)"}
        )
        assert response.status_code == 200
        data = response.json()
        
        celebrity = data.get("celebrity", {})
        assert celebrity.get("name") == "Pink (singer)", "Should return Pink (singer)"
        
        # Verify wiki_url is correct
        wiki_url = celebrity.get("wiki_url", "")
        assert "Pink_(singer)" in wiki_url or "pink_(singer)" in wiki_url.lower(), \
            f"Wiki URL should point to Pink (singer), got {wiki_url}"
        
        # CRITICAL: Verify tier is A (not D as currently stored in DB)
        tier = celebrity.get("tier")
        price = celebrity.get("price")
        
        # Note: This test may fail if the bug is not fixed
        # Expected: tier=A, price>=12.0
        # Current bug: tier=D, price=0.6
        print(f"Pink (singer) - Tier: {tier}, Price: £{price}M")
        
        # These assertions document the expected behavior
        # If they fail, it indicates the bug is still present
        assert tier == "A", f"Pink (singer) should be A-list, got {tier} - BUG: DB has incorrect tier"
        assert price >= 12.0, f"Pink (singer) price should be >= £12M, got £{price}M - BUG: DB has incorrect price"
    
    def test_daniel_radcliffe_search(self):
        """POST /api/celebrity/search for Daniel Radcliffe should return correct tier/price"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Daniel Radcliffe"}
        )
        assert response.status_code == 200
        data = response.json()
        
        celebrity = data.get("celebrity", {})
        tier = celebrity.get("tier")
        price = celebrity.get("price")
        
        print(f"Daniel Radcliffe - Tier: {tier}, Price: £{price}M")
        
        assert tier == "A", f"Daniel Radcliffe should be A-list, got {tier}"
        assert price >= 12.0, f"Daniel Radcliffe price should be >= £12M, got £{price}M"


class TestHotCelebsEndpoint:
    """Test hot-celebs endpoint tier/price consistency"""
    
    def test_hot_celebs_returns_data(self):
        """GET /api/hot-celebs should return celebrities"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        hot_celebs = data.get("hot_celebs", [])
        assert len(hot_celebs) > 0, "Should return at least one hot celebrity"
    
    def test_hot_celebs_tier_price_consistency(self):
        """All hot celebs should have consistent tier and price"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        hot_celebs = data.get("hot_celebs", [])
        
        inconsistent = []
        for celeb in hot_celebs:
            name = celeb.get("name", "Unknown")
            tier = celeb.get("tier")
            price = celeb.get("price")
            base_price = celeb.get("base_price")
            
            if tier and price:
                expected_base = TIER_PRICE_MAP.get(tier, 2.5)
                
                # Check if base_price matches tier
                if base_price and abs(base_price - expected_base) > 0.5:
                    inconsistent.append({
                        "name": name,
                        "tier": tier,
                        "base_price": base_price,
                        "expected_base": expected_base,
                        "issue": "base_price doesn't match tier"
                    })
                
                # Check if final price is reasonable (base + up to 50% premium)
                if price < expected_base * 0.9:
                    inconsistent.append({
                        "name": name,
                        "tier": tier,
                        "price": price,
                        "expected_min": expected_base * 0.9,
                        "issue": "price too low for tier"
                    })
        
        if inconsistent:
            print(f"Found {len(inconsistent)} inconsistent celebrities:")
            for item in inconsistent:
                print(f"  - {item}")
        
        # Allow some inconsistencies due to news premiums, but flag if too many
        assert len(inconsistent) <= len(hot_celebs) * 0.2, \
            f"Too many tier/price inconsistencies: {len(inconsistent)}/{len(hot_celebs)}"


class TestPinkAliasMapping:
    """Test that Pink alias correctly maps to Pink (singer)"""
    
    def test_pink_alias_in_autocomplete(self):
        """Searching 'pink' should include Pink (singer) via alias mapping"""
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=pink")
        assert response.status_code == 200
        data = response.json()
        
        suggestions = data.get("suggestions", [])
        names = [s.get("name", "").lower() for s in suggestions]
        
        # Should have Pink (singer) in results
        has_pink_singer = any("pink (singer)" in name for name in names)
        assert has_pink_singer, f"Pink (singer) should be in results, got: {names}"
    
    def test_pnk_alias(self):
        """Searching 'p!nk' should also work (alias mapping)"""
        # Note: URL encoding for special characters
        response = requests.get(f"{BASE_URL}/api/autocomplete?q=p%21nk")
        # This may or may not work depending on implementation
        # Just verify no server error
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
