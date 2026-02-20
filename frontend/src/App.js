import { useEffect, useState, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Search, Crown, Film, Tv, Music, Trophy, Star, Share2, X, Copy, Check, TrendingUp, Minus, Plus, Users, Info, ChevronUp, Newspaper, ArrowLeftRight, Skull, Facebook } from "lucide-react";

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
  other: Users,
};

// Tier colors
const tierColors = {
  A: { bg: "bg-[#FFD700]", text: "text-black", label: "A-LIST" },
  B: { bg: "bg-[#C0C0C0]", text: "text-black", label: "B-LIST" },
  C: { bg: "bg-[#CD7F32]", text: "text-white", label: "C-LIST" },
  D: { bg: "bg-[#666666]", text: "text-white", label: "D-LIST" },
};

// Tier Badge Component
const TierBadge = ({ tier }) => {
  const tierStyle = tierColors[tier] || tierColors.D;
  return (
    <span className={`${tierStyle.bg} ${tierStyle.text} px-2 py-1 text-[10px] font-bold uppercase tracking-wider`}>
      {tierStyle.label}
    </span>
  );
};

// Player Count Banner
const PlayerCountBanner = ({ stats }) => {
  if (!stats) return null;
  return (
    <div className="bg-[#1A1A1A] border-b border-[#262626] py-2 px-4" data-testid="player-count-banner">
      <div className="max-w-7xl mx-auto flex justify-center items-center gap-6 text-sm">
        <span className="text-[#A1A1AA]">
          <span className="text-[#FFD700] font-bold">{stats.player_count.toLocaleString()}</span> Players
        </span>
        <span className="text-[#262626]">|</span>
        <span className="text-[#A1A1AA]">
          <span className="text-[#00F0FF] font-bold">{stats.celebrity_count.toLocaleString()}</span> Celebrities
        </span>
        <span className="text-[#262626]">|</span>
        <span className="text-[#A1A1AA]">
          Transfer Window: <span className="text-[#FF0099] font-bold">{stats.transfer_window}</span>
        </span>
      </div>
    </div>
  );
};

// Points Methodology Component
const PointsMethodology = ({ onClose }) => (
  <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
    <div className="bg-[#0A0A0A] border border-[#262626] max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-anton text-2xl uppercase text-[#FFD700]">How Points Are Calculated</h3>
          <button onClick={onClose} className="text-[#A1A1AA] hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>
        <p className="text-[#A1A1AA] mb-6">Celebrity Buzz Points are calculated based on media coverage and public interest:</p>
        
        <div className="space-y-4 mb-6">
          <div className="bg-[#1A1A1A] p-4">
            <h4 className="font-bold text-[#FF0099] mb-2">📰 News Mentions</h4>
            <p className="text-sm text-[#A1A1AA]">+1.0 point per article mentioning the celebrity</p>
          </div>
          <div className="bg-[#1A1A1A] p-4">
            <h4 className="font-bold text-[#FF0099] mb-2">🗞️ Tabloid Coverage</h4>
            <p className="text-sm text-[#A1A1AA]">+3.0 points per tabloid article (Daily Mail, The Sun, TMZ)</p>
          </div>
          <div className="bg-[#1A1A1A] p-4">
            <h4 className="font-bold text-[#FF0099] mb-2">📺 Broadsheet Coverage</h4>
            <p className="text-sm text-[#A1A1AA]">+2.0 points per quality press article (BBC, Guardian, Times)</p>
          </div>
          <div className="bg-[#1A1A1A] p-4">
            <h4 className="font-bold text-[#FF0099] mb-2">⚡ Controversy Bonus</h4>
            <p className="text-sm text-[#A1A1AA]"><span className="text-[#FFD700] font-bold">+25 points</span> per scandal/negative article!</p>
          </div>
          <div className="bg-[#1A1A1A] p-4">
            <h4 className="font-bold text-[#FF0099] mb-2">📱 Social Media Trending</h4>
            <p className="text-sm text-[#A1A1AA]">+5.0 points per trending event on social platforms</p>
          </div>
        </div>
        
        <h4 className="font-bold text-white mb-3">Tier Multipliers</h4>
        <div className="grid grid-cols-2 gap-2 mb-6">
          <div className="bg-[#FFD700] text-black p-2 text-center text-sm font-bold">A-LIST: 1.0x</div>
          <div className="bg-[#C0C0C0] text-black p-2 text-center text-sm font-bold">B-LIST: 1.2x</div>
          <div className="bg-[#CD7F32] text-white p-2 text-center text-sm font-bold">C-LIST: 1.5x</div>
          <div className="bg-[#666666] text-white p-2 text-center text-sm font-bold">D-LIST: 2.0x</div>
        </div>
        
        <div className="bg-[#FF0099]/20 border border-[#FF0099] p-4 mb-4">
          <p className="text-sm"><strong>Example:</strong> A D-list celebrity with 10 tabloid mentions = 10 × 3.0 × 2.0 = <span className="text-[#FFD700] font-bold">60 points</span></p>
        </div>
        
        <div className="bg-[#333]/50 border border-[#444] p-4">
          <h4 className="font-bold text-white mb-2 flex items-center gap-2">
            <Skull className="w-5 h-5 text-[#888]" />
            Brown Bread Bonus 💀
          </h4>
          <p className="text-sm text-[#A1A1AA]">If one of your celebrities passes away, you receive a <span className="text-[#FFD700] font-bold">+100 bonus points</span>! Dark? Yes. Part of the game? Absolutely.</p>
        </div>
      </div>
    </div>
  </div>
);

// Today's News Component
const TodaysNews = ({ news }) => {
  if (!news || news.length === 0) return null;
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-6 mb-8" data-testid="todays-news">
      <h3 className="font-anton text-2xl uppercase tracking-tight text-[#FF0099] mb-4 flex items-center gap-2">
        <Newspaper className="w-6 h-6" />
        Today's Top Celeb News
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {news.slice(0, 8).map((item, idx) => (
          <a 
            key={idx} 
            href={item.url || "#"} 
            target="_blank" 
            rel="noopener noreferrer"
            className="bg-[#1A1A1A] p-4 hover:bg-[#222] transition-colors block group"
          >
            <p className="text-xs text-[#00F0FF] uppercase mb-1">{item.source}</p>
            <p className="font-bold text-sm text-white mb-2 line-clamp-2 group-hover:text-[#FF0099]">{item.headline}</p>
            <p className="text-xs text-[#A1A1AA] line-clamp-2">{item.summary}</p>
            <div className="flex justify-between items-center mt-2">
              <p className="text-xs text-[#FFD700]">{item.celebrity}</p>
              <span className="text-xs text-[#FF0099] opacity-0 group-hover:opacity-100 transition-opacity">Read →</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};

// Footer Component
const Footer = () => (
  <footer className="bg-[#050505] border-t border-[#262626] py-8 mt-16" data-testid="footer">
    <div className="max-w-7xl mx-auto px-4 text-center">
      <p className="text-sm text-[#A1A1AA] mb-4">
        Celebrity Buzz Index scores are calculated automatically based on media mentions and do not reflect personal opinions.
      </p>
      <p className="text-xs text-[#666]">
        © 2026 Celebrity Buzz Index. All rights reserved.
      </p>
    </div>
  </footer>
);

// Top Picked Celebrities Component
const TopPickedCelebs = ({ celebs, onSelect }) => {
  if (!celebs || celebs.length === 0) return null;
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="top-picked">
      <h4 className="font-anton text-lg uppercase tracking-tight text-[#00F0FF] mb-3 flex items-center gap-2">
        <TrendingUp className="w-5 h-5" />
        Most Picked
      </h4>
      <div className="space-y-2">
        {celebs.slice(0, 5).map((celeb, idx) => (
          <div 
            key={celeb.id} 
            className="flex items-center gap-3 p-2 hover:bg-[#1A1A1A] cursor-pointer"
            onClick={() => onSelect(celeb.name)}
          >
            <span className="text-[#FFD700] font-bold w-6">#{idx + 1}</span>
            <img 
              src={celeb.image} 
              alt={celeb.name}
              className="w-8 h-8 rounded-full object-cover"
              onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=32&background=FF0099&color=fff`; }}
            />
            <span className="text-sm flex-1 truncate">{celeb.name}</span>
            <span className="text-xs text-[#A1A1AA]">{celeb.times_picked} picks</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// Brown Bread Watch Component - Strategic picks for the +100 bonus!
const BrownBreadWatch = ({ watchList, onSelect }) => {
  if (!watchList || watchList.length === 0) return null;
  
  const getRiskColor = (risk) => {
    switch(risk) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'elevated': return 'bg-yellow-500';
      case 'moderate': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };
  
  const getRiskEmoji = (risk) => {
    switch(risk) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'elevated': return '🟡';
      case 'moderate': return '🟢';
      default: return '⚪';
    }
  };
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="brown-bread-watch">
      <h4 className="font-anton text-lg uppercase tracking-tight text-[#888] mb-3 flex items-center gap-2">
        <Skull className="w-5 h-5" />
        Brown Bread Watch
      </h4>
      <p className="text-xs text-[#666] mb-3">Strategic picks for the +100 bonus 💀</p>
      <div className="space-y-2">
        {watchList.slice(0, 6).map((celeb) => (
          <div 
            key={celeb.id} 
            className="flex items-center gap-3 p-2 hover:bg-[#1A1A1A] cursor-pointer"
            onClick={() => onSelect(celeb.name)}
          >
            <span className="text-lg" title={`Risk: ${celeb.risk_level}`}>
              {getRiskEmoji(celeb.risk_level)}
            </span>
            <img 
              src={celeb.image} 
              alt={celeb.name}
              className="w-8 h-8 rounded-full object-cover grayscale"
              onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=32&background=666&color=fff`; }}
            />
            <div className="flex-1 min-w-0">
              <span className="text-sm truncate block">{celeb.name}</span>
              <span className="text-xs text-[#666]">Age {celeb.age}</span>
            </div>
            <span className="text-xs text-[#FFD700]">£{celeb.price}M</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// How It Works Component
const HowItWorks = ({ onShowMethodology }) => (
  <div className="bg-[#0A0A0A] border border-[#262626] p-6 mb-8" data-testid="how-it-works">
    <div className="flex justify-between items-center mb-4">
      <h3 className="font-anton text-2xl uppercase tracking-tight text-[#FFD700]">How It Works</h3>
      <button 
        onClick={onShowMethodology}
        className="flex items-center gap-2 text-[#00F0FF] hover:text-white text-sm"
        data-testid="show-methodology-btn"
      >
        <Info className="w-4 h-4" />
        How Points Work
      </button>
    </div>
    <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FF0099] flex items-center justify-center mx-auto mb-2">
          <Search className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm mb-1">1. Search</h4>
        <p className="text-xs text-[#A1A1AA]">Find any celebrity worldwide</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#00F0FF] flex items-center justify-center mx-auto mb-2">
          <Star className="w-5 h-5 text-black" />
        </div>
        <h4 className="font-space font-bold text-sm mb-1">2. Check Tier</h4>
        <p className="text-xs text-[#A1A1AA]">A-list £18M, D-list £3M</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FFD700] flex items-center justify-center mx-auto mb-2">
          <Plus className="w-5 h-5 text-black" />
        </div>
        <h4 className="font-space font-bold text-sm mb-1">3. Build Team</h4>
        <p className="text-xs text-[#A1A1AA]">£50M budget</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FF5500] flex items-center justify-center mx-auto mb-2">
          <ArrowLeftRight className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm mb-1">4. Transfer</h4>
        <p className="text-xs text-[#A1A1AA]">1 swap per week</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#8B5CF6] flex items-center justify-center mx-auto mb-2">
          <Skull className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm mb-1">5. Brown Bread</h4>
        <p className="text-xs text-[#A1A1AA]">+100 if celeb dies!</p>
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
          <span key={idx} className="ticker-item flex items-center gap-3">
            <img 
              src={celeb.image || `https://ui-avatars.com/api/?name=${celeb.name}&size=40&background=FF0099&color=fff`}
              alt={celeb.name}
              className="w-10 h-10 rounded-full object-cover border-2 border-black shadow-lg"
              onError={(e) => {
                e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=40&background=FF0099&color=fff`;
              }}
            />
            <span className="font-bold">{celeb.name}</span>
            <ChevronUp className="w-4 h-4 text-green-400" />
            <span className="text-[#FFD700]">{celeb.buzz_score?.toFixed(1)}</span>
            {celeb.tier && <TierBadge tier={celeb.tier} />}
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

// Search Bar Component with Autocomplete
const SearchBar = ({ onSearch, loading }) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const searchRef = useRef(null);
  const debounceRef = useRef(null);
  
  // Fetch autocomplete suggestions
  const fetchSuggestions = async (searchQuery) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    
    setLoadingSuggestions(true);
    try {
      const res = await axios.get(`${API}/autocomplete?q=${encodeURIComponent(searchQuery)}`);
      setSuggestions(res.data.suggestions || []);
    } catch (e) {
      console.error("Autocomplete error:", e);
      setSuggestions([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };
  
  // Debounced search
  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    setShowSuggestions(true);
    
    // Clear previous timeout
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    // Set new timeout for debounced search
    debounceRef.current = setTimeout(() => {
      fetchSuggestions(value);
    }, 300);
  };
  
  const handleSelectSuggestion = (suggestion) => {
    onSearch(suggestion.name);
    setQuery("");
    setSuggestions([]);
    setShowSuggestions(false);
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setQuery("");
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };
  
  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  
  return (
    <div ref={searchRef} className="search-container mb-8 px-4 relative">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setShowSuggestions(true)}
          placeholder="Search any celebrity worldwide..."
          className="search-input"
          data-testid="search-input"
        />
        <button type="submit" className="search-button" disabled={loading} data-testid="search-button">
          <Search className="w-5 h-5" />
        </button>
      </form>
      
      {/* Autocomplete Suggestions */}
      {showSuggestions && (suggestions.length > 0 || loadingSuggestions) && (
        <div className="absolute left-4 right-4 top-full mt-1 bg-[#0A0A0A] border border-[#262626] max-h-96 overflow-y-auto z-50" data-testid="autocomplete-dropdown">
          {loadingSuggestions ? (
            <div className="p-4 text-center text-[#A1A1AA]">Searching Wikipedia...</div>
          ) : (
            suggestions.map((suggestion, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectSuggestion(suggestion)}
                className="flex items-center gap-3 p-3 hover:bg-[#1A1A1A] cursor-pointer border-b border-[#262626] last:border-b-0"
                data-testid={`suggestion-${idx}`}
              >
                <img
                  src={suggestion.image}
                  alt={suggestion.name}
                  className="w-12 h-12 rounded object-cover"
                  onError={(e) => {
                    e.target.src = `https://ui-avatars.com/api/?name=${suggestion.name}&size=48&background=FF0099&color=fff`;
                  }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white truncate">{suggestion.name}</span>
                    <TierBadge tier={suggestion.estimated_tier} />
                  </div>
                  <p className="text-xs text-[#A1A1AA] truncate">{suggestion.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-[#FFD700] font-bold">£{suggestion.estimated_price}M</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
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
        {/* Tier badge top left */}
        <div className="absolute top-3 left-3">
          <TierBadge tier={celebrity.tier || "D"} />
        </div>
        <div className="celebrity-card-overlay">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="category-badge flex items-center gap-1">
              <Icon className="w-3 h-3" />
              {celebrity.category?.replace("_", " ")}
            </span>
            <span className="price-tag">£{celebrity.price}M</span>
          </div>
          <h3 className="font-anton text-2xl uppercase tracking-tight">{celebrity.name}</h3>
          <p className="text-sm text-[#A1A1AA] line-clamp-2 mt-1">{celebrity.bio?.slice(0, 100)}...</p>
          {celebrity.wiki_url && (
            <a 
              href={celebrity.wiki_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-[#00F0FF] hover:underline mt-2 inline-block"
              onClick={(e) => e.stopPropagation()}
            >
              View on Wikipedia →
            </a>
          )}
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
            <p className="text-sm text-[#A1A1AA]">
              {entry.celebrity_count} celebs
              {entry.brown_bread_bonus > 0 && (
                <span className="text-[#888] ml-2">💀 +{entry.brown_bread_bonus}</span>
              )}
            </p>
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

// Share Modal Component with WhatsApp, X, Facebook
const ShareModal = ({ team, onClose }) => {
  const [copied, setCopied] = useState(false);
  
  const shareText = `🌟 Check out my Celebrity Buzz team "${team?.team_name}"! Total Buzz: ${team?.total_points?.toFixed(1)} points! Can you beat me?`;
  const shareUrl = window.location.href;
  
  const handleTwitterShare = () => {
    const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`;
    window.open(twitterUrl, '_blank');
  };
  
  const handleFacebookShare = () => {
    const fbUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(shareText)}`;
    window.open(fbUrl, '_blank');
  };
  
  const handleWhatsAppShare = () => {
    const waUrl = `https://wa.me/?text=${encodeURIComponent(shareText + " " + shareUrl)}`;
    window.open(waUrl, '_blank');
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
          <X className="w-5 h-5" />
          Share on X / Twitter
        </button>
        
        <button onClick={handleFacebookShare} className="share-button bg-[#1877F2] text-white hover:bg-[#166FE5]" data-testid="share-facebook-btn">
          <Facebook className="w-5 h-5" />
          Share on Facebook
        </button>
        
        <button onClick={handleWhatsAppShare} className="share-button bg-[#25D366] text-white hover:bg-[#20BD5A]" data-testid="share-whatsapp-btn">
          Share on WhatsApp
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
  const [showMethodology, setShowMethodology] = useState(false);
  const [stats, setStats] = useState(null);
  const [todaysNews, setTodaysNews] = useState([]);
  const [topPicked, setTopPicked] = useState([]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/stats`);
      setStats(res.data);
    } catch (e) {
      console.error("Error fetching stats:", e);
    }
  }, []);

  // Fetch today's news
  const fetchTodaysNews = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/todays-news`);
      setTodaysNews(res.data.news || []);
    } catch (e) {
      console.error("Error fetching news:", e);
    }
  }, []);

  // Fetch top picked
  const fetchTopPicked = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/top-picked`);
      setTopPicked(res.data.top_picked || []);
    } catch (e) {
      console.error("Error fetching top picked:", e);
    }
  }, []);

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
      if (res.data.brown_bread_bonus) {
        toast.success(`Added ${celebrity.name} + 💀 Brown Bread Bonus!`, { duration: 5000 });
      } else {
        toast.success(`Added ${celebrity.name} to your team!`);
      }
      fetchLeaderboard();
      fetchTopPicked();
      fetchStats();
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
    fetchStats();
    fetchTodaysNews();
    fetchTopPicked();
  }, [fetchCategories, fetchTrending, initTeam, fetchLeaderboard, fetchStats, fetchTodaysNews, fetchTopPicked]);

  return (
    <div className="App">
      <Toaster position="top-right" theme="dark" richColors />
      <div className="noise-overlay"></div>
      
      <PlayerCountBanner stats={stats} />
      <Header />
      <TrendingTicker celebrities={trending} />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <HowItWorks onShowMethodology={() => setShowMethodology(true)} />
        <TodaysNews news={todaysNews} />
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
            <TopPickedCelebs celebs={topPicked} onSelect={searchCelebrity} />
            <Leaderboard entries={leaderboard} />
          </div>
        </div>
      </div>
      
      {/* Share Modal */}
      {showShareModal && team && (
        <ShareModal team={team} onClose={() => setShowShareModal(false)} />
      )}
      
      {/* Points Methodology Modal */}
      {showMethodology && (
        <PointsMethodology onClose={() => setShowMethodology(false)} />
      )}
      
      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
