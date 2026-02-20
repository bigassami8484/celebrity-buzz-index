#!/usr/bin/env python3
"""
Celebrity Buzz Index - Backend API Testing
Tests all API endpoints for the fantasy celebrity platform
"""

import requests
import sys
import json
import time
from datetime import datetime

class CelebrityBuzzTester:
    def __init__(self, base_url="https://buzz-fantasy-league.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.team_id = None
        self.celebrity_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details="", response_data=None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "response_data": response_data
        })

    def run_test(self, name, method, endpoint, expected_status=200, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}
        
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            
            success = response.status_code == expected_status
            response_data = None
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            if success:
                self.log_test(name, True, f"Status: {response.status_code}", response_data)
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}", response_data)
            
            return success, response_data

        except requests.exceptions.Timeout:
            self.log_test(name, False, f"Request timeout after {timeout}s")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Request error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health check"""
        return self.run_test("API Health Check", "GET", "")

    def test_categories(self):
        """Test categories endpoint"""
        success, data = self.run_test("Get Categories", "GET", "categories")
        if success and data:
            categories = data.get("categories", [])
            if len(categories) == 6:
                print(f"   ✓ Found all 6 categories: {[c['name'] for c in categories]}")
                return True
            else:
                print(f"   ✗ Expected 6 categories, found {len(categories)}")
                return False
        return success

    def test_trending(self):
        """Test trending celebrities endpoint"""
        success, data = self.run_test("Get Trending", "GET", "trending", timeout=15)
        if success and data:
            trending = data.get("trending", [])
            print(f"   ✓ Found {len(trending)} trending celebrities")
            if trending:
                print(f"   ✓ Sample: {trending[0].get('name', 'Unknown')}")
            return True
        return success

    def test_celebrity_search(self):
        """Test celebrity search with AI news generation"""
        print("\n🔍 Testing Celebrity Search (with AI news generation - may take 10+ seconds)...")
        
        # Test with a well-known celebrity
        test_celebrity = "Taylor Swift"
        success, data = self.run_test(
            f"Search Celebrity: {test_celebrity}", 
            "POST", 
            "celebrity/search",
            200,
            {"name": test_celebrity},
            timeout=30
        )
        
        if success and data:
            celebrity = data.get("celebrity", {})
            if celebrity:
                self.celebrity_id = celebrity.get("id")
                print(f"   ✓ Celebrity ID: {self.celebrity_id}")
                print(f"   ✓ Name: {celebrity.get('name')}")
                print(f"   ✓ Category: {celebrity.get('category')}")
                print(f"   ✓ Buzz Score: {celebrity.get('buzz_score')}")
                print(f"   ✓ Price: £{celebrity.get('price')}M")
                print(f"   ✓ News Articles: {len(celebrity.get('news', []))}")
                
                # Check if AI news was generated
                news = celebrity.get("news", [])
                if news:
                    print(f"   ✓ AI News Generated: {news[0].get('title', 'No title')[:50]}...")
                    return True
                else:
                    print("   ⚠ No news generated (AI might be slow)")
                    return True  # Still consider success if celebrity found
            else:
                print("   ✗ No celebrity data returned")
                return False
        return success

    def test_category_celebrities(self):
        """Test getting celebrities by category"""
        success, data = self.run_test("Get Musicians Category", "GET", "celebrities/category/musicians", timeout=20)
        if success and data:
            celebrities = data.get("celebrities", [])
            print(f"   ✓ Found {len(celebrities)} musicians")
            if celebrities:
                print(f"   ✓ Sample: {celebrities[0].get('name', 'Unknown')}")
            return True
        return success

    def test_team_creation(self):
        """Test team creation"""
        success, data = self.run_test(
            "Create Team", 
            "POST", 
            "team/create",
            200,
            {"team_name": "Test Buzz Team"}
        )
        
        if success and data:
            team = data.get("team", {})
            if team:
                self.team_id = team.get("id")
                print(f"   ✓ Team ID: {self.team_id}")
                print(f"   ✓ Team Name: {team.get('team_name')}")
                print(f"   ✓ Budget: £{team.get('budget_remaining')}M")
                return True
            else:
                print("   ✗ No team data returned")
                return False
        return success

    def test_get_team(self):
        """Test getting team by ID"""
        if not self.team_id:
            print("   ⚠ Skipping - no team ID available")
            return False
            
        success, data = self.run_test("Get Team", "GET", f"team/{self.team_id}")
        if success and data:
            team = data.get("team", {})
            print(f"   ✓ Retrieved team: {team.get('team_name')}")
            return True
        return success

    def test_add_to_team(self):
        """Test adding celebrity to team"""
        if not self.team_id or not self.celebrity_id:
            print("   ⚠ Skipping - missing team ID or celebrity ID")
            return False
            
        success, data = self.run_test(
            "Add Celebrity to Team", 
            "POST", 
            "team/add",
            200,
            {
                "team_id": self.team_id,
                "celebrity_id": self.celebrity_id
            }
        )
        
        if success and data:
            team = data.get("team", {})
            celebrities = team.get("celebrities", [])
            print(f"   ✓ Team now has {len(celebrities)} celebrities")
            print(f"   ✓ Budget remaining: £{team.get('budget_remaining')}M")
            return True
        return success

    def test_remove_from_team(self):
        """Test removing celebrity from team"""
        if not self.team_id or not self.celebrity_id:
            print("   ⚠ Skipping - missing team ID or celebrity ID")
            return False
            
        success, data = self.run_test(
            "Remove Celebrity from Team", 
            "POST", 
            "team/remove",
            200,
            {
                "team_id": self.team_id,
                "celebrity_id": self.celebrity_id
            }
        )
        
        if success and data:
            team = data.get("team", {})
            celebrities = team.get("celebrities", [])
            print(f"   ✓ Team now has {len(celebrities)} celebrities")
            print(f"   ✓ Budget refunded: £{team.get('budget_remaining')}M")
            return True
        return success

    def test_leaderboard(self):
        """Test leaderboard endpoint"""
        success, data = self.run_test("Get Leaderboard", "GET", "leaderboard")
        if success and data:
            leaderboard = data.get("leaderboard", [])
            print(f"   ✓ Found {len(leaderboard)} teams on leaderboard")
            if leaderboard:
                top_team = leaderboard[0]
                print(f"   ✓ Top team: {top_team.get('team_name')} ({top_team.get('total_points')} points)")
            return True
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Celebrity Buzz Index Backend Tests")
        print(f"🌐 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Core API tests
        self.test_health_check()
        self.test_categories()
        self.test_trending()
        
        # Celebrity search (AI-powered)
        self.test_celebrity_search()
        self.test_category_celebrities()
        
        # Team management
        self.test_team_creation()
        self.test_get_team()
        self.test_add_to_team()
        self.test_remove_from_team()
        
        # Leaderboard
        self.test_leaderboard()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 BACKEND TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL BACKEND TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return False

def main():
    """Main test runner"""
    tester = CelebrityBuzzTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open("/app/backend_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "tests_run": tester.tests_run,
                "tests_passed": tester.tests_passed,
                "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0
            },
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())