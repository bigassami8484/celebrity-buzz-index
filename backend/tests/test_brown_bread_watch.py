"""
Test cases for Brown Bread Watch feature:
- API endpoint returns list of elderly celebrities aged 60+
- Each celebrity has risk_level based on age
- Risk levels: critical (90+), high (80-89), elevated (70-79), moderate (60-69)
- Celebrities are sorted by age descending
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestBrownBreadWatchAPI:
    """Test Brown Bread Watch API endpoint"""
    
    def test_brown_bread_watch_endpoint_returns_200(self):
        """API endpoint should return 200 status"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_brown_bread_watch_returns_watch_list(self):
        """API should return watch_list array"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        assert 'watch_list' in data, "Response should contain 'watch_list' key"
        assert isinstance(data['watch_list'], list), "watch_list should be an array"
    
    def test_brown_bread_watch_celebrities_have_required_fields(self):
        """Each celebrity should have required fields"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list - need to seed elderly celebrities first")
        
        required_fields = ['id', 'name', 'age', 'risk_level', 'price', 'image']
        
        for celeb in watch_list:
            for field in required_fields:
                assert field in celeb, f"Celebrity '{celeb.get('name', 'unknown')}' missing field: {field}"
    
    def test_brown_bread_watch_all_celebrities_aged_60_plus(self):
        """All celebrities in watch list should be 60+ years old"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        for celeb in watch_list:
            age = celeb.get('age', 0)
            assert age >= 60, f"Celebrity '{celeb.get('name')}' age {age} should be >= 60"
    
    def test_brown_bread_watch_risk_levels_are_valid(self):
        """Risk levels should be one of: critical, high, elevated, moderate"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        valid_risk_levels = ['critical', 'high', 'elevated', 'moderate', 'low']
        
        for celeb in watch_list:
            risk_level = celeb.get('risk_level', '')
            assert risk_level in valid_risk_levels, f"Celebrity '{celeb.get('name')}' has invalid risk_level: {risk_level}"


class TestBrownBreadRiskLevelCalculation:
    """Test risk level calculation based on age"""
    
    def test_critical_risk_for_age_90_plus(self):
        """Celebrities aged 90+ should have 'critical' risk level"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        critical_celebs = [c for c in watch_list if c.get('age', 0) >= 90]
        
        for celeb in critical_celebs:
            assert celeb.get('risk_level') == 'critical', \
                f"Celebrity '{celeb.get('name')}' aged {celeb.get('age')} should have 'critical' risk, got '{celeb.get('risk_level')}'"
    
    def test_high_risk_for_age_80_to_89(self):
        """Celebrities aged 80-89 should have 'high' risk level"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        high_risk_celebs = [c for c in watch_list if 80 <= c.get('age', 0) < 90]
        
        for celeb in high_risk_celebs:
            assert celeb.get('risk_level') == 'high', \
                f"Celebrity '{celeb.get('name')}' aged {celeb.get('age')} should have 'high' risk, got '{celeb.get('risk_level')}'"
    
    def test_elevated_risk_for_age_70_to_79(self):
        """Celebrities aged 70-79 should have 'elevated' risk level"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        elevated_risk_celebs = [c for c in watch_list if 70 <= c.get('age', 0) < 80]
        
        for celeb in elevated_risk_celebs:
            assert celeb.get('risk_level') == 'elevated', \
                f"Celebrity '{celeb.get('name')}' aged {celeb.get('age')} should have 'elevated' risk, got '{celeb.get('risk_level')}'"
    
    def test_moderate_risk_for_age_60_to_69(self):
        """Celebrities aged 60-69 should have 'moderate' risk level"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        moderate_risk_celebs = [c for c in watch_list if 60 <= c.get('age', 0) < 70]
        
        for celeb in moderate_risk_celebs:
            assert celeb.get('risk_level') == 'moderate', \
                f"Celebrity '{celeb.get('name')}' aged {celeb.get('age')} should have 'moderate' risk, got '{celeb.get('risk_level')}'"


class TestBrownBreadWatchSorting:
    """Test that watch list is sorted by age descending"""
    
    def test_watch_list_sorted_by_age_descending(self):
        """Watch list should be sorted by age in descending order"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) < 2:
            pytest.skip("Need at least 2 celebrities to test sorting")
        
        ages = [c.get('age', 0) for c in watch_list]
        assert ages == sorted(ages, reverse=True), \
            f"Watch list should be sorted by age descending. Got ages: {ages}"


class TestBrownBreadWatchCelebrityData:
    """Test specific celebrity data in watch list"""
    
    def test_seeded_elderly_celebrities_present(self):
        """Seeded elderly celebrities should be in watch list"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        # Check for at least some of the seeded celebrities
        names = [c.get('name', '').lower() for c in watch_list]
        
        # At least one of these should be present
        expected_celebs = ['michael caine', 'judi dench', 'morgan freeman', 'ian mckellen', 'al pacino', 'paul mccartney', 'robert de niro']
        found = [name for name in expected_celebs if name in names]
        
        assert len(found) > 0, f"Expected at least one of {expected_celebs} in watch list. Found names: {names}"
    
    def test_celebrities_have_images(self):
        """All celebrities should have image URLs"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        for celeb in watch_list:
            image = celeb.get('image', '')
            assert image and len(image) > 0, f"Celebrity '{celeb.get('name')}' should have an image URL"
    
    def test_celebrities_have_prices(self):
        """All celebrities should have valid prices"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        for celeb in watch_list:
            price = celeb.get('price', 0)
            assert price > 0, f"Celebrity '{celeb.get('name')}' should have a positive price, got {price}"
    
    def test_celebrities_are_not_deceased(self):
        """All celebrities in watch list should be living (not deceased)"""
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        for celeb in watch_list:
            is_deceased = celeb.get('is_deceased', False)
            assert is_deceased == False, f"Celebrity '{celeb.get('name')}' should not be deceased in watch list"


class TestBrownBreadWatchIntegration:
    """Integration tests for Brown Bread Watch with other features"""
    
    def test_watch_list_celebrity_can_be_searched(self):
        """Celebrities from watch list should be searchable"""
        # First get a celebrity from watch list
        response = requests.get(f"{BASE_URL}/api/brown-bread-watch")
        assert response.status_code == 200
        
        data = response.json()
        watch_list = data.get('watch_list', [])
        
        if len(watch_list) == 0:
            pytest.skip("No celebrities in watch list")
        
        # Search for the first celebrity
        celeb_name = watch_list[0].get('name')
        search_response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": celeb_name}
        )
        
        assert search_response.status_code == 200, f"Search for '{celeb_name}' should return 200"
        
        search_data = search_response.json()
        found_celeb = search_data.get('celebrity', {})
        assert found_celeb.get('name') == celeb_name, f"Search should return celebrity '{celeb_name}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
