const fs = require("fs");
const path = require("path");
const fetch = require("node-fetch");

const CACHE_DIR = path.join(__dirname, "cache");
const CACHE_DURATION = 1000 * 60 * 60 * 24 * 30; // 30 days

if (!fs.existsSync(CACHE_DIR)) fs.mkdirSync(CACHE_DIR);

async function fetchWikipediaData(name) {
  const url = `https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(name)}`;
  const res = await fetch(url);
  return res.json();
}

async function fetchNewsArticles(name) {
  // Replace with your existing news sources API or scraping
  // Example dummy data:
  return [
    { title: `${name} latest news headline`, link: "https://news.example.com" },
    { title: `More about ${name}`, link: "https://news.example.com" },
  ];
}

// Example scoring / tier logic (adjust your current formula)
function calculateScore(data) {
  const score = data.extract ? Math.min(data.extract.length, 100) : 50;
  let tier = "D";
  if (score > 80) tier = "A";
  else if (score > 60) tier = "B";
  else if (score > 40) tier = "C";
  return { score, tier };
}

async function getCelebrityData(name) {
  const filePath = path.join(CACHE_DIR, `${name}.json`);

  // Check cache
  if (fs.existsSync(filePath)) {
    const cached = JSON.parse(fs.readFileSync(filePath));
    if (Date.now() - new Date(cached.lastUpdated).getTime() < CACHE_DURATION) {
      return cached;
    }
  }

  // Fetch Wikipedia
  const wikiData = await fetchWikipediaData(name);

  // Skull logic: only true if valid death date
  const deathDate = wikiData.deathDate ? new Date(wikiData.deathDate) : null;
  const isDead = deathDate && deathDate < new Date();

  // Image (medium size)
  const imageUrl = wikiData.thumbnail?.source
    ? wikiData.thumbnail.source.replace(/\/[0-9]+px-/, "/500px-")
    : "";

  // Wikipedia score & tier
  const { score: wikipediaScore, tier } = calculateScore(wikiData);

  // News
  const news = await fetchNewsArticles(name);

  const celebData = {
    name: wikiData.title,
    image: imageUrl,
    wikipediaScore,
    tier,
    isDead,
    news,
    lastUpdated: new Date().toISOString(),
  };

  // Save cache
  fs.writeFileSync(filePath, JSON.stringify(celebData));

  return celebData;
}

// Export API handler (Express / serverless compatible)
module.exports = async function handler(req, res) {
  try {
    const { name } = req.query;
    if (!name) return res.status(400).json({ error: "Missing celeb name" });

    const data = await getCelebrityData(name);
    res.status(200).json(data);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Failed to fetch celeb" });
  }
};
