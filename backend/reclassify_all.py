#!/usr/bin/env python3
"""
Background script to reclassify all celebrities using the new Wikipedia-based tier system.
Run with: nohup python3 reclassify_all.py > /tmp/reclassify.log 2>&1 &
"""
import asyncio
import httpx
import os
import sys
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import re

# Load environment
load_dotenv('/app/backend/.env')

# MongoDB connection
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]

async def calculate_tier_from_wikipedia_data(name: str, http_client: httpx.AsyncClient) -> dict:
    """
    Calculate celebrity tier based on objective Wikipedia metrics.
    """
    headers = {
        "User-Agent": "CelebrityBuzzIndex/1.0 (https://celebrity-buzz-index.com) httpx/0.27"
    }
    
    result = {
        "tier": "D",
        "price": 1.0,
        "score": 0,
        "metrics": {
            "language_count": 0,
            "years_active": 0,
            "award_score": 0,
            "bio_length": 0,
            "career_score": 0
        },
        "reasoning": []
    }
    
    try:
        # 1. Get language count from Wikidata
        wikidata_search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={name}&language=en&format=json&limit=1"
        wd_response = await http_client.get(wikidata_search_url, timeout=10.0, headers=headers)
        
        if wd_response.status_code == 200:
            wd_data = wd_response.json()
            if wd_data.get("search"):
                entity_id = wd_data["search"][0].get("id")
                
                entity_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&ids={entity_id}&props=sitelinks&format=json"
                entity_response = await http_client.get(entity_url, timeout=10.0, headers=headers)
                
                if entity_response.status_code == 200:
                    entity_data = entity_response.json()
                    entities = entity_data.get("entities", {})
                    if entity_id in entities:
                        sitelinks = entities[entity_id].get("sitelinks", {})
                        wiki_langs = sum(1 for k in sitelinks.keys() if k.endswith("wiki") and not k.startswith("common"))
                        result["metrics"]["language_count"] = wiki_langs
        
        # 2. Get Wikipedia bio
        wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&titles={name.replace(' ', '_')}&prop=extracts&exintro=false&explaintext=true&format=json"
        wiki_response = await http_client.get(wiki_url, timeout=10.0, headers=headers)
        
        bio = ""
        if wiki_response.status_code == 200:
            wiki_data = wiki_response.json()
            pages = wiki_data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    bio = page_data.get("extract", "")
                    result["metrics"]["bio_length"] = len(bio)
        
        bio_lower = bio.lower() if bio else ""
        
        # 3. Years active
        current_year = datetime.now().year
        career_patterns = [
            r'career\s+(?:began|started|launched)\s+(?:in\s+)?(\d{4})',
            r'debut(?:ed)?\s+(?:in\s+)?(\d{4})',
            r'first\s+(?:appeared|role|film|album|single)\s+(?:in\s+)?(\d{4})',
            r'since\s+(\d{4})',
            r'(\d{4})\s*[-–]\s*present',
            r'active\s+(?:since\s+)?(\d{4})',
        ]
        
        career_start = None
        for pattern in career_patterns:
            match = re.search(pattern, bio_lower)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= current_year:
                    if career_start is None or year < career_start:
                        career_start = year
        
        if career_start:
            result["metrics"]["years_active"] = current_year - career_start
        
        # 4. Award scoring
        major_awards = [
            ("oscar", 30), ("academy award", 30), ("grammy", 25), ("emmy", 25), ("tony", 20),
            ("golden globe", 20), ("bafta", 20), ("pulitzer", 25), ("nobel", 35),
            ("olympic gold", 30), ("olympic", 20), ("world champion", 25), ("world cup", 25),
            ("super bowl", 20), ("mvp", 15), ("all-star", 10), ("hall of fame", 25),
            ("knighted", 15), ("dame", 15), ("cbe", 10), ("mbe", 8), ("obe", 8),
            ("lifetime achievement", 20), ("legend", 10), ("icon", 8),
            ("billboard", 15), ("number one", 12), ("platinum", 10), ("multi-platinum", 15),
            ("bestselling", 15), ("best-selling", 15), ("highest-grossing", 20),
            ("forbes", 10), ("time 100", 15), ("influential", 8),
        ]
        
        award_score = 0
        for award, points in major_awards:
            if award in bio_lower:
                count = bio_lower.count(award)
                award_score += points * min(count, 3)
        
        result["metrics"]["award_score"] = award_score
        
        # 5. Career milestone scoring
        career_indicators = {
            "reality television": -10, "reality tv": -10, "influencer": -15, "social media personality": -15,
            "tiktok": -10, "youtube personality": -10, "instagram": -8, "contestant": -5,
            "appeared on": -3, "dating show": -10, "love island": -8, "big brother": -8,
            "the only way is essex": -8, "made in chelsea": -5, "geordie shore": -8,
            "starring role": 10, "leading role": 10, "critically acclaimed": 15,
            "box office": 15, "blockbuster": 15, "worldwide": 10, "international": 8,
            "legendary": 15, "iconic": 12, "pioneering": 12, "influential": 10,
            "million copies": 12, "billion": 20, "sold-out": 8, "arena tour": 10, "stadium": 12,
            "franchise": 10, "sequel": 5, "series regular": 8, "producer": 5, "director": 8,
            "founded": 10, "ceo": 8, "entrepreneur": 5,
            "prince of wales": 40, "princess of wales": 40, "duke": 25, "duchess": 25,
            "king": 35, "queen": 35, "royal family": 30, "heir": 20, "throne": 20,
            "president": 30, "prime minister": 30, "senator": 15, "governor": 15,
            "billionaire": 25, "philanthropist": 10,
        }
        
        career_score = 0
        for indicator, points in career_indicators.items():
            if indicator in bio_lower:
                career_score += points
        
        result["metrics"]["career_score"] = career_score
        
        # 6. Calculate final score
        lang_count = result["metrics"]["language_count"]
        years_active = result["metrics"]["years_active"]
        award_score = result["metrics"]["award_score"]
        bio_length = result["metrics"]["bio_length"]
        career_score = result["metrics"]["career_score"]
        
        total_score = 0
        
        # Language editions (max 40 points)
        if lang_count >= 80:
            total_score += 40
        elif lang_count >= 50:
            total_score += 30
        elif lang_count >= 30:
            total_score += 20
        elif lang_count >= 15:
            total_score += 10
        
        # Years active (max 25 points)
        if years_active >= 30:
            total_score += 25
        elif years_active >= 20:
            total_score += 20
        elif years_active >= 10:
            total_score += 12
        elif years_active >= 5:
            total_score += 5
        
        # Awards (max 45 points)
        if award_score >= 100:
            total_score += 45
        elif award_score >= 60:
            total_score += 35
        elif award_score >= 40:
            total_score += 25
        elif award_score >= 20:
            total_score += 15
        elif award_score >= 10:
            total_score += 8
        
        # Career quality
        total_score += career_score
        
        # Bio length bonus
        if bio_length >= 10000:
            total_score += 15
        elif bio_length >= 5000:
            total_score += 8
        elif bio_length >= 3000:
            total_score += 5
        
        result["score"] = total_score
        
        # Determine tier
        if total_score >= 70:
            result["tier"] = "A"
            result["price"] = 10.0 + min(2.0, (total_score - 70) / 15)
        elif total_score >= 45:
            result["tier"] = "B"
            result["price"] = 5.0 + ((total_score - 45) / 25) * 3
        elif total_score >= 20:
            result["tier"] = "C"
            result["price"] = 2.0 + ((total_score - 20) / 25) * 2
        else:
            result["tier"] = "D"
            result["price"] = 0.5 + max(0, (total_score / 20)) * 1
        
        result["price"] = round(min(12.0, max(0.5, result["price"])), 1)
        
    except Exception as e:
        print(f"Error calculating tier for {name}: {e}")
    
    return result


async def reclassify_all_celebrities():
    """Reclassify all celebrities in the database."""
    print(f"[{datetime.now()}] Starting full celebrity reclassification...")
    
    # Get all celebrities
    all_celebs = await db.celebrities.find(
        {},
        {"_id": 0, "id": 1, "name": 1, "tier": 1, "price": 1}
    ).to_list(2000)
    
    total = len(all_celebs)
    print(f"Found {total} celebrities to process")
    
    processed = 0
    tier_changes = {"A": 0, "B": 0, "C": 0, "D": 0}
    changes_made = 0
    
    async with httpx.AsyncClient() as http_client:
        for i, celeb in enumerate(all_celebs):
            celeb_id = celeb.get("id")
            name = celeb.get("name", "")
            old_tier = celeb.get("tier", "D")
            
            try:
                result = await calculate_tier_from_wikipedia_data(name, http_client)
                new_tier = result["tier"]
                new_price = result["price"]
                
                tier_changes[new_tier] += 1
                
                if old_tier != new_tier:
                    changes_made += 1
                    if changes_made <= 50:  # Log first 50 changes
                        print(f"  [{i+1}/{total}] {name}: {old_tier}→{new_tier} (score: {result['score']})")
                
                # Update celebrity
                await db.celebrities.update_one(
                    {"id": celeb_id},
                    {
                        "$set": {
                            "tier": new_tier,
                            "price": new_price,
                            "tier_score": result["score"],
                            "tier_metrics": result["metrics"],
                            "tier_updated_at": datetime.now(timezone.utc).isoformat()
                        }
                    }
                )
                
                processed += 1
                
                # Progress update every 100
                if processed % 100 == 0:
                    print(f"[{datetime.now()}] Progress: {processed}/{total} ({processed*100//total}%)")
                
                # Rate limiting
                await asyncio.sleep(0.4)
                
            except Exception as e:
                print(f"Error processing {name}: {e}")
    
    print(f"\n[{datetime.now()}] Reclassification complete!")
    print(f"Processed: {processed}/{total}")
    print(f"Changes made: {changes_made}")
    print(f"Final tier distribution: A={tier_changes['A']}, B={tier_changes['B']}, C={tier_changes['C']}, D={tier_changes['D']}")
    
    # Store summary
    await db.scheduled_tasks.insert_one({
        "task": "full_reclassification",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_processed": processed,
            "changes_made": changes_made,
            "tier_distribution": tier_changes
        }
    })


if __name__ == "__main__":
    asyncio.run(reclassify_all_celebrities())
