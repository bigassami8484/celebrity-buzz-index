import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Search, Crown, Film, Tv, Music, Trophy, Star, Share2, X, Copy, Check, TrendingUp, Minus, Plus } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Category Icons
const categoryIcons = {
  movie_stars: Film,
  tv_actors: Tv,
  musicians: Music,
  athletes: Trophy,
  royals: Crown,
  reality_tv: Star,
  other: Star,
};

// How It Works Component
const HowItWorks = () => (
  <div className="bg-[#0A0A0A] border border-[#262626] p-6 mb-8" data-testid="how-it-works">
    <h3 className="font-anton text-2xl uppercase tracking-tight mb-4 text-[#FFD700]">How It Works</h3>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="text-center">
        <div className="w-12 h-12 bg-[#FF0099] flex items-center justify-center mx-auto mb-3">
          <Search className="w-6 h-6 text-white" />
        </div>
        <h4 className="font-space font-bold text-lg mb-2">1. Search & Browse</h4>
        <p className="text-sm text-[#A1A1AA]">Find celebrities by name or browse categories like Royals, Reality TV, Musicians & more</p>
      </div>
      <div className="text-center">
        <div className="w-12 h-12 bg-[#00F0FF] flex items-center justify-center mx-auto mb-3">
          <Plus className="w-6 h-6 text-black" />
        </div>
        <h4 className="font-space font-bold text-lg mb-2">2. Build Your Team</h4>
        <p className="text-sm text-[#A1A1AA]">Spend your £50M budget wisely. High buzz = higher price!</p>
      </div>
      <div className="text-center">
        <div className="w-12 h-12 bg-[#FFD700] flex items-center justify-center mx-auto mb-3">
          <Trophy className="w-6 h-6 text-black" />
        </div>
        <h4 className="font-space font-bold text-lg mb-2">3. Climb the Leaderboard</h4>
        <p className="text-sm text-[#A1A1AA]">Earn points based on your celebrities' buzz scores. Share & compete!</p>
      </div>
    </div>
  </div>
);

// Header Component
const Header = () => (
  <header className="py-8 px-4 text-center">
    <h1 className="font-anton text-5xl md:text-7xl tracking-tighter uppercase header-title" data-testid="main-title">
      <span className="text-[#FFD700]">C</span>
      <span className="text-[#FF0099]">e</span>
      <span>l</span>
      <span className="text-[#FF0099]">e</span>
      <span>b</span>
      <span className="text-[#00F0FF]">r</span>
      <span>i</span>
      <span className="text-[#FF0099]">t</span>
      <span>y</span>
      <span className="mx-4"></span>
      <span className="text-[#FFD700]">B</span>
      <span className="text-[#FF0099]">u</span>
      <span>z</span>
      <span className="text-[#00F0FF]">z</span>
      <span className="mx-4"></span>
      <span className="text-[#FFD700]">I</span>
      <span className="text-[#FF0099]">n</span>
      <span>d</span>
      <span className="text-[#00F0FF]">e</span>
      <span>x</span>
    </h1>
    <p className="font-space text-[#A1A1AA] mt-4 text-sm uppercase tracking-[4px]">
      Build Your Dream Celebrity Team
    </p>
  </header>
);

// Trending Ticker Component with Images
const TrendingTicker = ({ celebrities }) => {
  if (!celebrities.length) return null;
  
  const doubled = [...celebrities, ...celebrities];
  
  return (
    <div className="ticker-container" data-testid="trending-ticker">
      <div className="ticker-content">
        {doubled.map((celeb, idx) => (
          <span key={idx} className="ticker-item flex items-center gap-2">
            <img 
              src={celeb.image || `https://ui-avatars.com/api/?name=${celeb.name}&size=32&background=FF0099&color=fff`}
              alt={celeb.name}
              className="w-8 h-8 rounded-full object-cover border-2 border-black"
              onError={(e) => {
                e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=32&background=FF0099&color=fff`;
              }}
            />
            {celeb.name} <TrendingUp className="inline w-4 h-4 mx-1" /> {celeb.buzz_score?.toFixed(1)}
          </span>
        ))}
      </div>
    </div>
  );
};

// Category Filter Component
const CategoryFilter = ({ categories, activeCategory, onSelect }) => (
  <div className="flex flex-wrap gap-3 justify-center py-6 px-4" data-testid="category-filter">
    <button
      className={`category-pill ${!activeCategory ? 'active' : ''}`}
      onClick={() => onSelect(null)}
      data-testid="category-all"
    >
      All
    </button>
    {categories.map((cat) => {
      const Icon = categoryIcons[cat.id] || Star;
      return (
        <button
          key={cat.id}
          className={`category-pill flex items-center gap-2 ${activeCategory === cat.id ? 'active' : ''}`}
          onClick={() => onSelect(cat.id)}
          data-testid={`category-${cat.id}`}
        >
          <Icon className="w-4 h-4" />
          {cat.name}
        </button>
      );
    })}
  </div>
);

// Search Bar Component
const SearchBar = ({ onSearch, loading }) => {
  const [query, setQuery] = useState("");
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setQuery("");
    }
  };
  
  return (
    <form onSubmit={handleSubmit} className="search-container mb-8 px-4">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search any celebrity..."
        className="search-input"
        data-testid="search-input"
      />
      <button type="submit" className="search-button" disabled={loading} data-testid="search-button">
        <Search className="w-5 h-5" />
      </button>
    </form>
  );
};

// Celebrity Card Component
const CelebrityCard = ({ celebrity, onAdd, isInTeam, canAfford }) => {
  const [showNews, setShowNews] = useState(false);
  const Icon = categoryIcons[celebrity.category] || Star;
  
  return (
    <div 
      className="celebrity-card"
      data-testid={`celebrity-card-${celebrity.id}`}
    >
      <div 
        className="relative overflow-hidden"
        onMouseEnter={() => setShowNews(true)}
        onMouseLeave={() => setShowNews(false)}
      >
        <img
          src={celebrity.image || `https://ui-avatars.com/api/?name=${celebrity.name}&size=400&background=FF0099&color=fff`}
          alt={celebrity.name}
          className="celebrity-card-image"
          onError={(e) => {
            e.target.src = `https://ui-avatars.com/api/?name=${celebrity.name}&size=400&background=FF0099&color=fff`;
          }}
        />
        <div className="buzz-score" data-testid={`buzz-score-${celebrity.id}`}>
          {celebrity.buzz_score?.toFixed(1)}
        </div>
        <div className="celebrity-card-overlay">
          <div className="flex items-center gap-2 mb-2">
            <span className="category-badge flex items-center gap-1">
              <Icon className="w-3 h-3" />
              {celebrity.category?.replace("_", " ")}
            </span>
            <span className="price-tag">£{celebrity.price}M</span>
          </div>
          <h3 className="font-anton text-2xl uppercase tracking-tight">{celebrity.name}</h3>
          <p className="text-sm text-[#A1A1AA] line-clamp-2 mt-1">{celebrity.bio?.slice(0, 100)}...</p>
        </div>
        
        {/* News Panel on Hover */}
        <div className={`news-panel ${showNews ? 'opacity-100' : ''}`}>
          <h4 className="font-anton text-lg uppercase mb-4 text-[#00F0FF]">Latest News</h4>
          {celebrity.news?.length > 0 ? (
            celebrity.news.slice(0, 4).map((item, idx) => (
              <div key={idx} className="news-item">
                <p className="news-title">{item.title}</p>
                <p className="news-source">{item.source} • {item.date}</p>
              </div>
            ))
          ) : (
            <p className="text-[#A1A1AA] text-sm">No recent news available</p>
          )}
        </div>
      </div>
      
      {/* Button outside of hover zone */}
      <div className="p-4 bg-[#0A0A0A]">
        <button
          onClick={() => onAdd(celebrity)}
          disabled={isInTeam || !canAfford}
          className="add-button"
          data-testid={`add-btn-${celebrity.id}`}
        >
          {isInTeam ? "In Team" : !canAfford ? "Can't Afford" : "Add to Team"}
        </button>
      </div>
    </div>
  );
};

// Loading Card Skeleton
const LoadingCard = () => (
  <div className="celebrity-card">
    <div className="skeleton h-[280px]"></div>
    <div className="p-4">
      <div className="skeleton h-6 w-3/4 mb-2"></div>
      <div className="skeleton h-4 w-full mb-4"></div>
      <div className="skeleton h-10 w-full"></div>
    </div>
  </div>
);

// Team Panel Component
const TeamPanel = ({ team, onRemove, onShare }) => {
  if (!team) return null;
  
  return (
    <div className="team-panel" data-testid="team-panel">
      <div className="team-header">
        <div>
          <h3 className="font-anton text-2xl uppercase tracking-tight">{team.team_name}</h3>
          <p className="text-sm text-[#A1A1AA] font-space">
            {team.celebrities?.length || 0} celebrities • {team.total_points?.toFixed(1)} points
          </p>
        </div>
        <div className="text-right">
          <div className="budget-display" data-testid="budget-display">
            £{team.budget_remaining}M
          </div>
          <p className="text-xs text-[#A1A1AA] uppercase tracking-wider">Budget Left</p>
        </div>
      </div>
      
      {team.celebrities?.length > 0 ? (
        <>
          {team.celebrities.map((celeb) => (
            <div key={celeb.celebrity_id} className="team-celeb" data-testid={`team-celeb-${celeb.celebrity_id}`}>
              <img 
                src={celeb.image || `https://ui-avatars.com/api/?name=${celeb.name}&size=100&background=FF0099&color=fff`} 
                alt={celeb.name}
                className="team-celeb-image"
              />
              <div className="flex-1">
                <p className="font-bold">{celeb.name}</p>
                <p className="text-sm text-[#A1A1AA]">
                  <span className="text-[#FFD700]">£{celeb.price}M</span> • 
                  <span className="text-[#FF0099] ml-1">{celeb.buzz_score?.toFixed(1)} buzz</span>
                </p>
              </div>
              <button 
                onClick={() => onRemove(celeb.celebrity_id)}
                className="remove-btn"
                data-testid={`remove-btn-${celeb.celebrity_id}`}
              >
                <Minus className="w-5 h-5" />
              </button>
            </div>
          ))}
          <button 
            onClick={onShare}
            className="add-button flex items-center justify-center gap-2 mt-4"
            data-testid="share-team-btn"
          >
            <Share2 className="w-4 h-4" />
            Share Team
          </button>
        </>
      ) : (
        <p className="text-center text-[#A1A1AA] py-8">
          Search and add celebrities to build your team!
        </p>
      )}
    </div>
  );
};

// Leaderboard Component
const Leaderboard = ({ entries }) => (
  <div className="leaderboard" data-testid="leaderboard">
    <h3 className="font-anton text-2xl uppercase tracking-tight mb-4">Leaderboard</h3>
    {entries.length > 0 ? (
      entries.slice(0, 10).map((entry, idx) => (
        <div key={entry.team_id} className="leaderboard-row">
          <span className={`leaderboard-rank ${idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : ''}`}>
            #{idx + 1}
          </span>
          <div className="flex-1 ml-4">
            <p className="font-bold">{entry.team_name}</p>
            <p className="text-sm text-[#A1A1AA]">{entry.celebrity_count} celebrities</p>
          </div>
          <div className="font-space font-bold text-xl text-[#FF0099]">
            {entry.total_points?.toFixed(1)}
          </div>
        </div>
      ))
    ) : (
      <p className="text-center text-[#A1A1AA] py-4">No teams yet. Be the first!</p>
    )}
  </div>
);

// Share Modal Component
const ShareModal = ({ team, onClose }) => {
  const [copied, setCopied] = useState(false);
  
  const shareText = `Check out my Celebrity Buzz team "${team?.team_name}"! Total Buzz: ${team?.total_points?.toFixed(1)} points! 🌟`;
  const shareUrl = window.location.href;
  
  const handleTwitterShare = () => {
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
    window.open(twitterUrl, '_blank');
  };
  
  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      toast.error("Failed to copy");
    }
  };
  
  return (
    <div className="share-modal-overlay" onClick={onClose} data-testid="share-modal">
      <div className="share-modal" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-anton text-2xl uppercase">Share Your Team</h3>
          <button onClick={onClose} className="text-[#A1A1AA] hover:text-white" data-testid="close-share-modal">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="bg-[#1A1A1A] p-4 mb-6">
          <p className="text-sm text-[#A1A1AA] mb-2">Preview:</p>
          <p className="font-space">{shareText}</p>
        </div>
        
        <button onClick={handleTwitterShare} className="share-button share-twitter" data-testid="share-twitter-btn">
          Share on X / Twitter
        </button>
        
        <button onClick={handleCopy} className="share-button share-copy" data-testid="share-copy-btn">
          {copied ? <Check className="w-5 h-5" /> : <Copy className="w-5 h-5" />}
          {copied ? "Copied!" : "Copy to Clipboard"}
        </button>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [celebrities, setCelebrities] = useState([]);
  const [trending, setTrending] = useState([]);
  const [team, setTeam] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/categories`);
      setCategories(res.data.categories || []);
    } catch (e) {
      console.error("Error fetching categories:", e);
    }
  }, []);

  // Fetch trending
  const fetchTrending = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/trending`);
      setTrending(res.data.trending || []);
    } catch (e) {
      console.error("Error fetching trending:", e);
    }
  }, []);

  // Fetch celebrities by category
  const fetchCelebritiesByCategory = useCallback(async (category) => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/celebrities/category/${category}`);
      setCelebrities(res.data.celebrities || []);
    } catch (e) {
      console.error("Error fetching celebrities:", e);
      toast.error("Failed to load celebrities");
    } finally {
      setLoading(false);
    }
  }, []);

  // Search celebrity
  const searchCelebrity = async (name) => {
    setSearchLoading(true);
    try {
      const res = await axios.post(`${API}/celebrity/search`, { name });
      const celeb = res.data.celebrity;
      if (celeb) {
        setCelebrities(prev => {
          const exists = prev.find(c => c.id === celeb.id);
          if (exists) return prev;
          return [celeb, ...prev];
        });
        toast.success(`Found ${celeb.name}!`);
      }
    } catch (e) {
      console.error("Search error:", e);
      toast.error("Celebrity not found");
    } finally {
      setSearchLoading(false);
    }
  };

  // Create or get team
  const initTeam = useCallback(async () => {
    // Check localStorage for existing team
    const storedTeamId = localStorage.getItem("teamId");
    if (storedTeamId) {
      try {
        const res = await axios.get(`${API}/team/${storedTeamId}`);
        setTeam(res.data.team);
        return;
      } catch (e) {
        localStorage.removeItem("teamId");
      }
    }
    
    // Create new team
    try {
      const res = await axios.post(`${API}/team/create`, { team_name: "My Buzz Team" });
      const newTeam = res.data.team;
      localStorage.setItem("teamId", newTeam.id);
      setTeam(newTeam);
    } catch (e) {
      console.error("Error creating team:", e);
    }
  }, []);

  // Fetch leaderboard
  const fetchLeaderboard = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/leaderboard`);
      setLeaderboard(res.data.leaderboard || []);
    } catch (e) {
      console.error("Error fetching leaderboard:", e);
    }
  }, []);

  // Add celebrity to team
  const addToTeam = async (celebrity) => {
    if (!team) return;
    
    try {
      const res = await axios.post(`${API}/team/add`, {
        team_id: team.id,
        celebrity_id: celebrity.id
      });
      setTeam(res.data.team);
      toast.success(`Added ${celebrity.name} to your team!`);
      fetchLeaderboard();
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to add celebrity");
    }
  };

  // Remove celebrity from team
  const removeFromTeam = async (celebrityId) => {
    if (!team) return;
    
    try {
      const res = await axios.post(`${API}/team/remove`, {
        team_id: team.id,
        celebrity_id: celebrityId
      });
      setTeam(res.data.team);
      toast.success("Removed from team");
      fetchLeaderboard();
    } catch (e) {
      toast.error("Failed to remove celebrity");
    }
  };

  // Check if celebrity is in team
  const isInTeam = (celebrityId) => {
    return team?.celebrities?.some(c => c.celebrity_id === celebrityId) || false;
  };

  // Check if can afford celebrity
  const canAfford = (price) => {
    return (team?.budget_remaining || 0) >= price;
  };

  // Category change handler
  const handleCategoryChange = (category) => {
    setActiveCategory(category);
    if (category) {
      fetchCelebritiesByCategory(category);
    } else {
      setCelebrities([]);
    }
  };

  // Initial load
  useEffect(() => {
    fetchCategories();
    fetchTrending();
    initTeam();
    fetchLeaderboard();
  }, [fetchCategories, fetchTrending, initTeam, fetchLeaderboard]);

  return (
    <div className="App">
      <Toaster position="top-right" theme="dark" richColors />
      <div className="noise-overlay"></div>
      
      <Header />
      <TrendingTicker celebrities={trending} />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <SearchBar onSearch={searchCelebrity} loading={searchLoading} />
        <CategoryFilter 
          categories={categories} 
          activeCategory={activeCategory} 
          onSelect={handleCategoryChange} 
        />
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-8">
          {/* Celebrity Grid */}
          <div className="lg:col-span-8">
            {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map(i => <LoadingCard key={i} />)}
              </div>
            ) : celebrities.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6" data-testid="celebrity-grid">
                {celebrities.map(celeb => (
                  <CelebrityCard
                    key={celeb.id}
                    celebrity={celeb}
                    onAdd={addToTeam}
                    isInTeam={isInTeam(celeb.id)}
                    canAfford={canAfford(celeb.price)}
                  />
                ))}
              </div>
            ) : (
              <div className="text-center py-16">
                <h3 className="font-anton text-3xl text-[#A1A1AA] uppercase">
                  {activeCategory ? "Loading celebrities..." : "Select a category or search"}
                </h3>
                <p className="text-[#666] mt-2">
                  Choose a category above or search for any celebrity
                </p>
              </div>
            )}
          </div>
          
          {/* Sidebar */}
          <div className="lg:col-span-4 space-y-6">
            <TeamPanel 
              team={team} 
              onRemove={removeFromTeam}
              onShare={() => setShowShareModal(true)}
            />
            <Leaderboard entries={leaderboard} />
          </div>
        </div>
      </div>
      
      {/* Share Modal */}
      {showShareModal && team && (
        <ShareModal team={team} onClose={() => setShowShareModal(false)} />
      )}
    </div>
  );
}

export default App;
