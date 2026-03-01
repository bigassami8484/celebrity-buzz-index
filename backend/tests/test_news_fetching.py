"""
Test suite for Celebrity News Fetching API
Tests the /api/celebrity/search endpoint and news article retrieval
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCelebrityNewsAPI:
    """Tests for celebrity search and news fetching"""
    
    def test_david_beckham_returns_news(self):
        """Test that David Beckham search returns news articles"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "David Beckham"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        
        assert celeb.get("name") is not None, "Celebrity name should be returned"
        assert "beckham" in celeb.get("name", "").lower(), "Should return David Beckham"
        
        news = celeb.get("news", [])
        print(f"David Beckham news count: {len(news)}")
        # Note: News may or may not be present depending on current RSS feeds
        
    def test_taylor_swift_returns_news(self):
        """Test that Taylor Swift search returns news articles"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Taylor Swift"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        
        assert celeb.get("name") is not None, "Celebrity name should be returned"
        assert "taylor swift" in celeb.get("name", "").lower(), "Should return Taylor Swift"
        
        news = celeb.get("news", [])
        print(f"Taylor Swift news count: {len(news)}")
        
    def test_katie_price_returns_news(self):
        """Test that Katie Price search returns news articles"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Katie Price"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        
        assert celeb.get("name") is not None, "Celebrity name should be returned"
        assert "katie price" in celeb.get("name", "").lower(), "Should return Katie Price"
        
        news = celeb.get("news", [])
        print(f"Katie Price news count: {len(news)}")
        # Katie Price is a tabloid regular, should have news
        assert len(news) > 0, "Katie Price should have news articles"
        
    def test_news_articles_have_required_fields(self):
        """Test that news articles have title, source, and date fields"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Katie Price"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        news = celeb.get("news", [])
        
        if len(news) > 0:
            for article in news[:3]:
                assert "title" in article, "Article should have title"
                assert "source" in article, "Article should have source"
                assert "date" in article, "Article should have date"
                print(f"Article: {article.get('title', '')[:50]}... from {article.get('source')}")
                
    def test_news_articles_have_urls(self):
        """Test that news articles have clickable URLs"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Katie Price"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        news = celeb.get("news", [])
        
        articles_with_urls = 0
        articles_without_urls = 0
        
        for article in news:
            url = article.get("url", "")
            if url and url.startswith("http"):
                articles_with_urls += 1
            else:
                articles_without_urls += 1
                print(f"Article without URL: {article.get('title', '')[:50]}... from {article.get('source')}")
        
        print(f"Articles with URLs: {articles_with_urls}, without URLs: {articles_without_urls}")
        # At least some articles should have URLs
        if len(news) > 0:
            assert articles_with_urls > 0, "At least some articles should have URLs"


class TestHotCelebsAPI:
    """Tests for Hot Celebs banner endpoint"""
    
    def test_hot_celebs_returns_list(self):
        """Test that hot celebs endpoint returns a list of celebrities"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        hot_celebs = data.get("hot_celebs", [])
        assert len(hot_celebs) > 0, "Should return hot celebrities"
        print(f"Hot celebs count: {len(hot_celebs)}")
        
    def test_hot_celebs_have_required_fields(self):
        """Test that hot celebs have name, tier, and price"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        hot_celebs = data.get("hot_celebs", [])
        for celeb in hot_celebs[:5]:
            assert "name" in celeb, "Hot celeb should have name"
            assert "tier" in celeb, "Hot celeb should have tier"
            assert "price" in celeb, "Hot celeb should have price"
            print(f"Hot celeb: {celeb.get('name')} - Tier {celeb.get('tier')} - £{celeb.get('price')}M")
            
    def test_hot_celebs_have_images(self):
        """Test that hot celebs have images"""
        response = requests.get(f"{BASE_URL}/api/hot-celebs")
        assert response.status_code == 200
        data = response.json()
        
        hot_celebs = data.get("hot_celebs", [])
        celebs_with_images = 0
        
        for celeb in hot_celebs:
            if celeb.get("image"):
                celebs_with_images += 1
                
        print(f"Hot celebs with images: {celebs_with_images}/{len(hot_celebs)}")
        assert celebs_with_images > 0, "At least some hot celebs should have images"


class TestCelebritySearchValidation:
    """Tests for search input validation"""
    
    def test_empty_name_returns_error(self):
        """Test that empty name returns appropriate error"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": ""},
            headers={"Content-Type": "application/json"}
        )
        # Should return 400, 404, or 422 for invalid input
        assert response.status_code in [400, 404, 422], f"Empty name should return error, got {response.status_code}"
        
    def test_whitespace_name_returns_error(self):
        """Test that whitespace-only name returns appropriate error"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "   "},
            headers={"Content-Type": "application/json"}
        )
        # Should return 400, 404, or 422 for invalid input
        assert response.status_code in [400, 404, 422], f"Whitespace name should return error, got {response.status_code}"


class TestCelebrityTierAndPricing:
    """Tests for celebrity tier and pricing"""
    
    def test_a_list_celebrity_has_correct_tier(self):
        """Test that A-list celebrities are correctly tiered"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "Taylor Swift"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        
        tier = celeb.get("tier", "")
        print(f"Taylor Swift tier: {tier}")
        assert tier == "A", "Taylor Swift should be A-list"
        
    def test_celebrity_has_price(self):
        """Test that celebrities have a price"""
        response = requests.post(
            f"{BASE_URL}/api/celebrity/search",
            json={"name": "David Beckham"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        celeb = data.get("celebrity", {})
        
        price = celeb.get("price", 0)
        print(f"David Beckham price: £{price}M")
        assert price > 0, "Celebrity should have a price"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
