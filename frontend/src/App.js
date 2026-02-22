import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import { Toaster, toast } from "sonner";
import { UserPlus, X, Users, Search, Newspaper, TrendingUp, TrendingDown, Minus } from "lucide-react";

// API
import {
  fetchCategories as fetchCategoriesAPI,
  fetchTrending as fetchTrendingAPI,
  fetchCelebritiesByCategory as fetchCelebritiesByCategoryAPI,
  searchCelebrityAPI,
  fetchStats as fetchStatsAPI,
  fetchTodaysNews as fetchTodaysNewsAPI,
  fetchTopPicked as fetchTopPickedAPI,
  fetchHotCelebs as fetchHotCelebsAPI,
  fetchBrownBreadWatch as fetchBrownBreadWatchAPI,
  fetchPriceAlerts as fetchPriceAlertsAPI,
  fetchHotStreaks as fetchHotStreaksAPI,
  fetchLeaderboard as fetchLeaderboardAPI,
  fetchHallOfFame as fetchHallOfFameAPI,
  fetchCustomOptions as fetchCustomOptionsAPI,
  createTeam,
  getTeam,
  addToTeamAPI,
  removeFromTeamAPI,
  customizeTeamAPI,
  fetchTeamLeagues,
  createLeagueAPI,
  joinLeagueAPI,
  fetchLeagueLeaderboard,
  checkAuthStatus,
  logoutAPI
} from "./api";

// Components
import { TierBadge, LoadingCard, CategoryFilter } from "./components/common";
import { AuthModal, AuthCallback, UserMenu, SaveTeamPrompt } from "./components/auth/index.jsx";
import { Header, Footer, TransferWindowBanner, HowItWorks } from "./components/layout";
import { 
  SearchBar, 
  CelebrityCard, 
  HotCelebsBanner, 
  TopPickedCelebs, 
  BrownBreadWatch,
  TodaysNews 
} from "./components/celebrities";
import { TeamPanel, TeamCustomizeModal } from "./components/team";
import { LeaguePanel, LeagueDetailModal, Leaderboard } from "./components/leagues/index.jsx";
import { 
  ShareModal, 
  PointsMethodology, 
  PriceHistoryModal, 
  HallOfFameModal,
  PriceAlerts,
  HotStreaks 
} from "./components/modals/index.jsx";

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
  const [showMobileTeam, setShowMobileTeam] = useState(false);
  const [stats, setStats] = useState(null);
  const [todaysNews, setTodaysNews] = useState([]);
  const [topPicked, setTopPicked] = useState([]);
  const [brownBreadWatch, setBrownBreadWatch] = useState([]);
  const [hotCelebs, setHotCelebs] = useState([]);
  const [priceAlerts, setPriceAlerts] = useState([]);
  const [hotStreaks, setHotStreaks] = useState([]);
  const [isTransferWindowOpen, setIsTransferWindowOpen] = useState(false);
  
  // Search result floating card state
  const [searchedCeleb, setSearchedCeleb] = useState(null);
  
  // Auth state
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);
  
  // Price History Modal state
  const [showPriceHistory, setShowPriceHistory] = useState(false);
  const [priceHistoryCeleb, setPriceHistoryCeleb] = useState(null);
  
  // League state
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [leagueLeaderboard, setLeagueLeaderboard] = useState([]);
  
  // Hall of Fame state
  const [showHallOfFame, setShowHallOfFame] = useState(false);
  const [hallOfFame, setHallOfFame] = useState([]);
  
  // Team customization state
  const [showCustomize, setShowCustomize] = useState(false);
  const [customOptions, setCustomOptions] = useState({ colors: [], icons: [] });
  
  // Save team prompt state
  const [showSavePrompt, setShowSavePrompt] = useState(false);
  const [savePromptDismissed, setSavePromptDismissed] = useState(false);
  
  // Check for OAuth callback session_id in URL fragment on mount
  const hasSessionId = window.location.hash?.includes('session_id=');
  
  // Show save prompt when guest has celebrities in team
  useEffect(() => {
    if (!user && team?.celebrities?.length > 0 && !savePromptDismissed) {
      const timer = setTimeout(() => {
        setShowSavePrompt(true);
      }, 3000);
      return () => clearTimeout(timer);
    } else {
      setShowSavePrompt(false);
    }
  }, [user, team, savePromptDismissed]);
  
  // Auth handlers
  const handleAuthSuccess = useCallback((userData) => {
    setUser(userData);
    setIsProcessingAuth(false);
    toast.success(`Welcome, ${userData.name}!`);
  }, []);
  
  const handleAuthError = useCallback((error) => {
    setIsProcessingAuth(false);
    toast.error(error || "Authentication failed");
  }, []);
  
  const handleLogout = useCallback(async () => {
    try {
      await logoutAPI();
      setUser(null);
      toast.success("Signed out successfully");
    } catch (error) {
      console.error("Logout error:", error);
      setUser(null);
    }
  }, []);
  
  // Check existing session on mount
  const checkAuth = useCallback(async () => {
    if (window.location.hash?.includes('session_id=')) {
      setIsProcessingAuth(true);
      return;
    }
    
    try {
      const res = await checkAuthStatus();
      if (res.is_authenticated && res.user) {
        setUser(res.user);
        // If user has a team linked to their account, use that
        if (res.team) {
          setTeam(res.team);
          localStorage.setItem("teamId", res.team.id);
          fetchTeamLeaguesData(res.team.id);
          fetchPriceAlerts(res.team.id);
          fetchHotStreaks(res.team.id);
        }
      }
    } catch (error) {
      console.log("Not authenticated");
    }
  }, [fetchTeamLeaguesData, fetchPriceAlerts, fetchHotStreaks]);
  
  // Handler to show price history
  const handleShowPriceHistory = (celebrityName) => {
    setPriceHistoryCeleb(celebrityName);
    setShowPriceHistory(true);
  };

  // Fetch functions using API module
  const fetchStats = useCallback(async () => {
    try {
      const data = await fetchStatsAPI();
      setStats(data);
    } catch (e) {
      console.error("Error fetching stats:", e);
    }
  }, []);

  const fetchTodaysNews = useCallback(async () => {
    try {
      const news = await fetchTodaysNewsAPI();
      setTodaysNews(news);
    } catch (e) {
      console.error("Error fetching news:", e);
    }
  }, []);

  const fetchTopPicked = useCallback(async () => {
    try {
      const picked = await fetchTopPickedAPI();
      setTopPicked(picked);
    } catch (e) {
      console.error("Error fetching top picked:", e);
    }
  }, []);

  const fetchHotCelebs = useCallback(async () => {
    try {
      console.log("Fetching hot celebs from API...");
      const celebs = await fetchHotCelebsAPI();
      console.log("Hot celebs received:", celebs?.length || 0);
      setHotCelebs(celebs || []);
    } catch (e) {
      console.error("Error fetching hot celebs:", e);
      setHotCelebs([]);
    }
  }, []);

  const fetchBrownBreadWatch = useCallback(async () => {
    try {
      const watchList = await fetchBrownBreadWatchAPI();
      setBrownBreadWatch(watchList);
    } catch (e) {
      console.error("Error fetching brown bread watch:", e);
    }
  }, []);

  const fetchPriceAlerts = useCallback(async (teamId) => {
    if (!teamId) return;
    try {
      const alerts = await fetchPriceAlertsAPI(teamId);
      setPriceAlerts(alerts);
    } catch (e) {
      console.error("Error fetching price alerts:", e);
    }
  }, []);

  const fetchHotStreaks = useCallback(async (teamId) => {
    if (!teamId) return;
    try {
      const streaks = await fetchHotStreaksAPI(teamId);
      setHotStreaks(streaks);
    } catch (e) {
      console.error("Error fetching hot streaks:", e);
    }
  }, []);

  const fetchTeamLeaguesData = useCallback(async (teamId) => {
    try {
      const leaguesData = await fetchTeamLeagues(teamId);
      setLeagues(leaguesData);
    } catch (e) {
      console.error("Error fetching leagues:", e);
    }
  }, []);

  const fetchHallOfFameData = useCallback(async () => {
    try {
      const hof = await fetchHallOfFameAPI();
      setHallOfFame(hof);
    } catch (e) {
      console.error("Error fetching hall of fame:", e);
    }
  }, []);

  const fetchCustomOptions = useCallback(async () => {
    try {
      const options = await fetchCustomOptionsAPI();
      setCustomOptions(options);
    } catch (e) {
      console.error("Error fetching customization options:", e);
    }
  }, []);

  // Customize team
  const customizeTeam = async (teamName, teamColor, teamIcon) => {
    if (!team) return;
    try {
      const updatedTeam = await customizeTeamAPI(team.id, teamName, teamColor, teamIcon);
      setTeam(updatedTeam);
      toast.success("Team customized! 🎨");
      setShowCustomize(false);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to customize team");
    }
  };

  // Create a new league
  const createLeague = async (name) => {
    if (!team) return;
    try {
      const newLeague = await createLeagueAPI(name, team.id);
      setLeagues(prev => [...prev, newLeague]);
      toast.success(`League "${name}" created! Share code: ${newLeague.code}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create league");
    }
  };

  // Join a league
  const joinLeague = async (code) => {
    if (!team) return;
    try {
      const result = await joinLeagueAPI(code, team.id);
      setLeagues(prev => [...prev, result.league]);
      toast.success(result.message);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to join league");
    }
  };

  // View league details
  const viewLeague = async (league) => {
    try {
      const lb = await fetchLeagueLeaderboard(league.id);
      setLeagueLeaderboard(lb);
      setSelectedLeague(league);
    } catch (e) {
      toast.error("Failed to load league");
    }
  };

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const cats = await fetchCategoriesAPI();
      setCategories(cats);
    } catch (e) {
      console.error("Error fetching categories:", e);
    }
  }, []);

  // Fetch trending
  const fetchTrending = useCallback(async () => {
    try {
      const trendingData = await fetchTrendingAPI();
      setTrending(trendingData);
    } catch (e) {
      console.error("Error fetching trending:", e);
    }
  }, []);

  // Fetch celebrities by category
  const fetchCelebritiesByCategory = useCallback(async (category) => {
    setLoading(true);
    try {
      const celebs = await fetchCelebritiesByCategoryAPI(category);
      setCelebrities(celebs);
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
      const celeb = await searchCelebrityAPI(name);
      if (celeb) {
        // Show in floating card instead of adding to grid
        setSearchedCeleb(celeb);
        toast.success(`Found ${celeb.name}!`);
      }
    } catch (e) {
      console.error("Search error:", e);
      toast.error("Celebrity not found");
    } finally {
      setSearchLoading(false);
    }
  };

  // Handle clicking on a celeb in the hot celebs ticker
  const handleCelebSearch = (name) => {
    searchCelebrity(name);
  };

  // Create or get team
  const initTeam = useCallback(async () => {
    // If we already have a team (from checkAuth), don't create a new one
    // This prevents overwriting a logged-in user's team
    const storedTeamId = localStorage.getItem("teamId");
    if (storedTeamId) {
      try {
        const existingTeam = await getTeam(storedTeamId);
        setTeam(prev => prev || existingTeam); // Don't overwrite if already set
        fetchTeamLeaguesData(storedTeamId);
        fetchPriceAlerts(storedTeamId);
        fetchHotStreaks(storedTeamId);
        return;
      } catch (e) {
        localStorage.removeItem("teamId");
      }
    }
    
    // Only create a new team if we don't have one
    try {
      const newTeam = await createTeam("My Buzz Team");
      localStorage.setItem("teamId", newTeam.id);
      setTeam(prev => prev || newTeam); // Don't overwrite if already set
    } catch (e) {
      console.error("Error creating team:", e);
    }
  }, [fetchTeamLeaguesData, fetchPriceAlerts, fetchHotStreaks]);

  // Fetch leaderboard
  const fetchLeaderboard = useCallback(async () => {
    try {
      const lb = await fetchLeaderboardAPI();
      setLeaderboard(lb);
    } catch (e) {
      console.error("Error fetching leaderboard:", e);
    }
  }, []);

  // Add celebrity to team
  const addToTeam = async (celebrity) => {
    if (!team) return;
    
    try {
      const result = await addToTeamAPI(team.id, celebrity.id);
      setTeam(result.team);
      if (result.brown_bread_bonus) {
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

  // Quick add from search autocomplete - searches first then adds
  const quickAddFromSearch = async (suggestion) => {
    if (!team) return;
    
    try {
      // First search for the celebrity to get full data
      const celeb = await searchCelebrityAPI(suggestion.name);
      if (celeb) {
        // Then add to team
        const result = await addToTeamAPI(team.id, celeb.id);
        setTeam(result.team);
        if (result.brown_bread_bonus) {
          toast.success(`Added ${celeb.name} + 💀 Brown Bread Bonus!`, { duration: 5000 });
        } else {
          toast.success(`Added ${celeb.name} to your team!`);
        }
        fetchLeaderboard();
        fetchTopPicked();
        fetchStats();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to add celebrity");
    }
  };

  // Remove celebrity from team
  const removeFromTeam = async (celebrityId) => {
    if (!team) return;
    
    // Check if team is locked
    if (team.is_locked && !isTransferWindowOpen) {
      toast.error("Team is locked! Wait for transfer window (Saturday)");
      return;
    }
    
    try {
      const updatedTeam = await removeFromTeamAPI(team.id, celebrityId);
      setTeam(updatedTeam);
      toast.success("Removed from team");
      fetchLeaderboard();
    } catch (e) {
      toast.error("Failed to remove celebrity");
    }
  };
  
  // Submit and lock team
  const submitTeam = async () => {
    if (!team) return;
    
    try {
      const response = await fetch(`${API}/api/team/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ team_id: team.id })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to submit team');
      }
      
      const data = await response.json();
      setTeam(data.team);
      toast.success("Team submitted and locked! 🔒");
    } catch (e) {
      toast.error(e.message || "Failed to submit team");
    }
  };
  
  // Fetch transfer window status
  const fetchTransferWindowStatus = async () => {
    try {
      const response = await fetch(`${API}/api/transfer-window-status`);
      const data = await response.json();
      setIsTransferWindowOpen(data.is_open);
    } catch (e) {
      console.error("Failed to fetch transfer window status");
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

  // Category change handler - always fetch fresh random celebrities
  const handleCategoryChange = (category) => {
    if (category) {
      // Clear current celebrities first to force re-render
      setCelebrities([]);
      setActiveCategory(category);
      // Small delay to ensure state is cleared before fetching
      setTimeout(() => {
        fetchCelebritiesByCategory(category);
      }, 50);
    } else {
      setActiveCategory(null);
      setCelebrities([]);
    }
  };

  // Initial load
  useEffect(() => {
    checkAuth();
    fetchCategories();
    fetchTrending();
    initTeam();
    fetchLeaderboard();
    fetchStats();
    fetchTodaysNews();
    fetchTopPicked();
    fetchBrownBreadWatch();
    fetchHotCelebs();
    fetchTransferWindowStatus();
  }, [checkAuth, fetchCategories, fetchTrending, initTeam, fetchLeaderboard, fetchStats, fetchTodaysNews, fetchTopPicked, fetchBrownBreadWatch, fetchHotCelebs]);

  // Auto-select first category when categories load
  useEffect(() => {
    if (categories.length > 0 && !activeCategory) {
      const firstCategory = categories[0].id;
      setActiveCategory(firstCategory);
      fetchCelebritiesByCategory(firstCategory);
    }
  }, [categories, activeCategory, fetchCelebritiesByCategory]);

  // Show AuthCallback when processing OAuth redirect
  if (hasSessionId || isProcessingAuth) {
    return (
      <div className="App">
        <AuthCallback 
          onAuthSuccess={handleAuthSuccess}
          onAuthError={handleAuthError}
        />
      </div>
    );
  }

  return (
    <div className="App">
      <Toaster position="top-right" theme="dark" richColors />
      <div className="noise-overlay"></div>
      
      {/* Auth Bar */}
      <div className="bg-[#0A0A0A] border-b border-[#262626] py-2 px-4">
        <div className="max-w-7xl mx-auto flex justify-end items-center">
          {user ? (
            <UserMenu user={user} onLogout={handleLogout} />
          ) : (
            <button
              onClick={() => setShowAuthModal(true)}
              className="flex items-center gap-2 bg-[#FF0099] hover:bg-[#e6008a] text-white px-4 py-2 text-sm font-bold transition-colors"
              data-testid="sign-in-btn"
            >
              <UserPlus className="w-4 h-4" />
              Sign In
            </button>
          )}
        </div>
      </div>
      
      <TransferWindowBanner stats={stats} />
      <Header />
      
      <div className="max-w-7xl mx-auto px-4">
        <HowItWorks onShowMethodology={() => setShowMethodology(true)} />
      </div>
      
      <HotCelebsBanner celebs={hotCelebs} onSelect={handleCelebSearch} />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <SearchBar 
          onSearch={searchCelebrity} 
          onQuickAdd={quickAddFromSearch}
          loading={searchLoading} 
          team={team}
        />
        
        {/* Floating Search Result Card */}
        {searchedCeleb && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={() => setSearchedCeleb(null)}>
            <div className="relative bg-[#0A0A0A] border border-[#FF0099] rounded-lg max-w-md w-full max-h-[90vh] overflow-y-auto shadow-2xl shadow-[#FF0099]/20" onClick={e => e.stopPropagation()}>
              {/* Close button */}
              <button 
                onClick={() => setSearchedCeleb(null)}
                className="absolute top-3 right-3 text-white/60 hover:text-white z-10"
              >
                <X className="w-6 h-6" />
              </button>
              
              <div className="p-6">
                {/* Image */}
                <div className="relative mb-4">
                  <img 
                    src={searchedCeleb.image} 
                    alt={searchedCeleb.name}
                    className="w-full h-48 object-cover rounded-lg"
                    onError={(e) => {
                      e.target.src = `https://ui-avatars.com/api/?name=${searchedCeleb.name}&size=400&background=1a1a1a&color=FF0099&bold=true`;
                    }}
                  />
                  <div className="absolute top-3 left-3">
                    <TierBadge tier={searchedCeleb.tier} />
                  </div>
                  <div className="absolute top-3 right-3 bg-[#FFD700] text-black px-3 py-1 rounded font-bold flex items-center gap-1">
                    £{searchedCeleb.price}M
                    {searchedCeleb.previous_week_price > 0 && (
                      <>
                        {searchedCeleb.price > searchedCeleb.previous_week_price ? (
                          <TrendingUp className="w-4 h-4 text-emerald-700" />
                        ) : searchedCeleb.price < searchedCeleb.previous_week_price ? (
                          <TrendingDown className="w-4 h-4 text-red-700" />
                        ) : (
                          <Minus className="w-4 h-4 text-gray-600" />
                        )}
                      </>
                    )}
                  </div>
                </div>
                
                {/* Info */}
                <h2 className="font-anton text-2xl text-white uppercase mb-2">
                  {searchedCeleb.name}
                  {searchedCeleb.is_deceased && <span className="ml-2" title="Deceased">💀</span>}
                </h2>
                <p className="text-[#A1A1AA] text-sm mb-4 line-clamp-2">{searchedCeleb.bio}</p>
                
                {/* Category tag */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="bg-[#FF0099]/20 text-[#FF0099] px-3 py-1 rounded text-xs uppercase">
                    {searchedCeleb.category?.replace(/_/g, ' ')}
                  </span>
                </div>
                
                {/* News Articles Section */}
                {searchedCeleb.news && searchedCeleb.news.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-[#00F0FF] text-sm font-bold uppercase mb-3 flex items-center gap-2">
                      <Newspaper className="w-4 h-4" />
                      Latest News
                    </h3>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {[...searchedCeleb.news]
                        .sort((a, b) => new Date(b.date) - new Date(a.date))
                        .slice(0, 5)
                        .map((article, idx) => (
                        <a 
                          key={idx} 
                          href={article.url || `https://www.google.com/search?q=${encodeURIComponent(article.title + ' ' + article.source)}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block bg-[#1A1A1A] p-3 rounded border border-[#262626] hover:border-[#FF0099] hover:bg-[#1A1A1A]/80 transition-all cursor-pointer group"
                          data-testid={`news-article-${idx}`}
                        >
                          <p className="text-white text-sm font-medium mb-1 line-clamp-2 group-hover:text-[#FF0099] transition-colors">{article.title}</p>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-[#A1A1AA] flex items-center gap-1">
                              {article.source}
                              {article.is_real && <span className="text-green-400" title="Real news">✓</span>}
                            </span>
                            <span className={`px-2 py-0.5 rounded ${
                              article.sentiment === 'positive' ? 'bg-green-500/20 text-green-400' :
                              article.sentiment === 'negative' ? 'bg-red-500/20 text-red-400' :
                              'bg-gray-500/20 text-gray-400'
                            }`}>
                              {article.sentiment}
                            </span>
                          </div>
                          <p className="text-[#666] text-xs mt-1">{article.date}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Add to Team Button */}
                <button
                  onClick={() => {
                    addToTeam(searchedCeleb);
                    setSearchedCeleb(null);
                  }}
                  disabled={isInTeam(searchedCeleb.id) || !canAfford(searchedCeleb.price)}
                  className={`w-full py-3 rounded font-bold uppercase transition-colors ${
                    isInTeam(searchedCeleb.id) 
                      ? 'bg-[#333] text-[#666] cursor-not-allowed' 
                      : !canAfford(searchedCeleb.price)
                        ? 'bg-[#333] text-[#666] cursor-not-allowed'
                        : 'bg-[#FF0099] hover:bg-[#e6008a] text-white'
                  }`}
                  data-testid="add-to-team-btn"
                >
                  {isInTeam(searchedCeleb.id) ? 'Already in Team' : !canAfford(searchedCeleb.price) ? "Can't Afford" : 'Add to Team'}
                </button>
              </div>
            </div>
          </div>
        )}
        
        <CategoryFilter 
          categories={categories} 
          activeCategory={activeCategory} 
          onSelect={handleCategoryChange} 
        />
        
        {/* Celebrity Grid */}
        <div className="mb-6">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => <LoadingCard key={i} />)}
            </div>
          ) : celebrities.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4" data-testid="celebrity-grid">
              {celebrities.map(celeb => (
                <CelebrityCard
                  key={celeb.id}
                  celebrity={celeb}
                  onAdd={addToTeam}
                  isInTeam={isInTeam(celeb.id)}
                  canAfford={canAfford(celeb.price)}
                  onShowPriceHistory={handleShowPriceHistory}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-8 bg-[#0A0A0A] border border-[#262626]">
              <div className="w-12 h-12 bg-[#1A1A1A] rounded-full flex items-center justify-center mx-auto mb-3">
                <Search className="w-6 h-6 text-[#666]" />
              </div>
              <h3 className="font-anton text-lg text-[#A1A1AA] uppercase">
                {activeCategory ? "Loading..." : "No Celebrities Yet"}
              </h3>
              <p className="text-xs text-[#666] mt-1">Search or select a category above</p>
            </div>
          )}
        </div>
        
        {/* Team Panel - Visible on ALL screens with responsive layout */}
        <div className="mb-6">
          <TeamPanel 
            team={team} 
            onRemove={removeFromTeam}
            onShare={() => setShowShareModal(true)}
            onCustomize={() => { fetchCustomOptions(); setShowCustomize(true); }}
            onSubmitTeam={submitTeam}
            isTransferWindowOpen={isTransferWindowOpen}
          />
        </div>
        
        <TodaysNews news={todaysNews} />
        
        {/* Hot Streaks - Full width */}
        <div className="mt-8">
          <HotStreaks streaks={hotStreaks} teamId={team?.id} />
        </div>
        
        {/* Brown Bread, Most Picked, Leaderboard - Show on ALL screen sizes */}
        <div className="mt-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <BrownBreadWatch watchList={brownBreadWatch} onSelect={searchCelebrity} />
            <TopPickedCelebs celebs={topPicked} onSelect={searchCelebrity} />
            <Leaderboard entries={leaderboard} />
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-8">
          {/* Main Content */}
          <div className="lg:col-span-8 space-y-6">
            <LeaguePanel
              team={team}
              leagues={leagues}
              onCreateLeague={createLeague}
              onJoinLeague={joinLeague}
              onViewLeague={viewLeague}
            />
          </div>
          
          {/* Sidebar */}
          <div className="lg:col-span-4 space-y-6">
            <PriceAlerts alerts={priceAlerts} teamId={team?.id} />
            
            {/* Hall of Fame Button */}
            <button
              onClick={() => { fetchHallOfFameData(); setShowHallOfFame(true); }}
              className="w-full bg-gradient-to-r from-[#FFD700] to-[#FF8C00] text-black font-bold py-3 px-4 flex items-center justify-center gap-2 hover:from-[#FFE44D] hover:to-[#FFA033] transition-all"
              data-testid="hall-of-fame-btn"
            >
              <span className="text-xl">🏆</span>
              Hall of Fame
            </button>
          </div>
        </div>
      </div>
      
      {/* Price History Modal */}
      {showPriceHistory && priceHistoryCeleb && (
        <PriceHistoryModal 
          celebrityName={priceHistoryCeleb} 
          onClose={() => {
            setShowPriceHistory(false);
            setPriceHistoryCeleb(null);
          }} 
        />
      )}
      
      {/* Share Modal */}
      {showShareModal && team && (
        <ShareModal team={team} onClose={() => setShowShareModal(false)} />
      )}
      
      {/* Points Methodology Modal */}
      {showMethodology && (
        <PointsMethodology onClose={() => setShowMethodology(false)} />
      )}
      
      {/* Auth Modal */}
      <AuthModal 
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onAuthSuccess={(userData) => {
          setUser(userData);
          setShowAuthModal(false);
          setShowSavePrompt(false);
          toast.success(`Welcome, ${userData.name}!`);
        }}
      />
      
      {/* Save Team Prompt for Guest Users */}
      <SaveTeamPrompt 
        isVisible={showSavePrompt}
        teamSize={team?.celebrities?.length || 0}
        onSave={() => {
          setShowSavePrompt(false);
          setShowAuthModal(true);
        }}
        onDismiss={() => {
          setShowSavePrompt(false);
          setSavePromptDismissed(true);
        }}
      />
      
      {/* League Detail Modal */}
      {selectedLeague && (
        <LeagueDetailModal
          league={selectedLeague}
          leaderboard={leagueLeaderboard}
          teamId={team?.id}
          onClose={() => setSelectedLeague(null)}
        />
      )}
      
      {/* Hall of Fame Modal */}
      {showHallOfFame && (
        <HallOfFameModal
          hallOfFame={hallOfFame}
          onClose={() => setShowHallOfFame(false)}
        />
      )}
      
      {/* Team Customize Modal */}
      {showCustomize && (
        <TeamCustomizeModal
          team={team}
          options={customOptions}
          onSave={customizeTeam}
          onClose={() => setShowCustomize(false)}
        />
      )}
      
      {/* Footer */}
      <Footer playerCount={stats?.player_count} />
    </div>
  );
}

export default App;
