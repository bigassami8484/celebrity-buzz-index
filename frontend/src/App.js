import { useEffect, useState, useCallback } from "react";
import "@/App.css";
import { Toaster, toast } from "sonner";
import { UserPlus, X, Users, Search, Newspaper, TrendingUp, TrendingDown, Minus, ExternalLink, Dice6, ChevronDown, ChevronUp, Info } from "lucide-react";

// API
import {
  API,
  AUTH_API,
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
  logoutAPI,
  feelingLucky
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
  TodaysNews,
  HotStreaks
} from "./components/celebrities";
import { TeamPanel, TeamCustomizeModal } from "./components/team";
import PriceWatch from "./components/team/PriceWatch";
import { LeaguePanel, LeagueDetailModal, Leaderboard } from "./components/leagues/index.jsx";
import { 
  ShareModal, 
  PointsMethodology, 
  PriceHistoryModal, 
  HallOfFameModal,
  PriceAlerts
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
  const [showTerms, setShowTerms] = useState(false);
  const [stats, setStats] = useState(null);
  const [todaysNews, setTodaysNews] = useState([]);
  const [topPicked, setTopPicked] = useState([]);
  const [brownBreadWatch, setBrownBreadWatch] = useState([]);
  const [hotCelebs, setHotCelebs] = useState([]);
  const [priceAlerts, setPriceAlerts] = useState([]);
  const [hotStreaks, setHotStreaks] = useState([]);
  const [isTransferWindowOpen, setIsTransferWindowOpen] = useState(false);
  
  // Mobile detection - check immediately and on mount
  const [isMobile, setIsMobile] = useState(() => {
    // Check immediately on initial render
    if (typeof window !== 'undefined') {
      return window.innerWidth < 768;
    }
    return false;
  });
  const [isLayoutReady, setIsLayoutReady] = useState(false);
  
  // Listen for resize and set layout ready immediately on mount
  useEffect(() => {
    // Immediately set correct mobile state and mark layout as ready
    const checkMobile = () => window.innerWidth < 768;
    setIsMobile(checkMobile());
    setIsLayoutReady(true);
    
    const handleResize = () => setIsMobile(checkMobile());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Search result floating card state
  const [searchedCeleb, setSearchedCeleb] = useState(null);
  
  // Auth state
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);
  
  // Price History Modal state
  const [showPriceHistory, setShowPriceHistory] = useState(false);
  const [priceHistoryCeleb, setPriceHistoryCeleb] = useState(null);
  
  // Price Watch state
  const [showPriceWatch, setShowPriceWatch] = useState(false);
  
  // League state
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [leagueLeaderboard, setLeagueLeaderboard] = useState([]);
  
  // Mobile collapsible tabs state
  const [mobileExpandedTab, setMobileExpandedTab] = useState(null);
  
  // How It Works collapsed state
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  
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
  const handleAuthSuccess = useCallback(async (userData) => {
    setUser(userData);
    setIsProcessingAuth(false);
    
    // Fetch user's team from the server after login
    try {
      const res = await checkAuthStatus();
      if (res.team) {
        // User has a team linked to their account - use it
        setTeam(res.team);
        localStorage.setItem("teamId", res.team.id);
        toast.success(`Welcome back, ${userData.name}! Your team is loaded.`);
      } else {
        // User doesn't have a team yet - link their current guest team
        const guestTeamId = localStorage.getItem("teamId");
        if (guestTeamId) {
          try {
            // Link the guest team to the user's account
            const linkResult = await fetch(`${AUTH_API}/guest/convert`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              credentials: 'include',
              body: JSON.stringify({ guest_team_id: guestTeamId })
            });
            if (linkResult.ok) {
              const data = await linkResult.json();
              setTeam(data.team);
              toast.success(`Welcome, ${userData.name}! Your team has been saved.`);
            } else {
              toast.success(`Welcome, ${userData.name}!`);
            }
          } catch (e) {
            console.error("Failed to link guest team:", e);
            toast.success(`Welcome, ${userData.name}!`);
          }
        } else {
          toast.success(`Welcome, ${userData.name}!`);
        }
      }
    } catch (e) {
      console.error("Error fetching user team:", e);
      toast.success(`Welcome, ${userData.name}!`);
    }
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
        }
      }
    } catch (error) {
      console.log("Not authenticated");
    }
  }, []);
  
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

  const fetchHotStreaks = useCallback(async () => {
    try {
      const streaks = await fetchHotStreaksAPI();
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
  }, []);

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

  // Add from Hot Celebs banner
  const addFromHotCelebs = async (hotCeleb) => {
    if (!team) {
      toast.error("Create a team first to add celebrities!");
      return;
    }
    
    try {
      // Search for the celebrity to get full data with ID
      const celeb = await searchCelebrityAPI(hotCeleb.name);
      if (celeb) {
        const result = await addToTeamAPI(team.id, celeb.id);
        setTeam(result.team);
        if (result.brown_bread_bonus) {
          toast.success(`🔥 Added ${celeb.name} + 💀 Brown Bread Bonus!`, { duration: 5000 });
        } else {
          toast.success(`🔥 Added ${celeb.name} to your team!`);
        }
        fetchLeaderboard();
        fetchTopPicked();
        fetchStats();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to add celebrity");
    }
  };

  // Feeling Lucky - auto-draft a random affordable celebrity
  const [feelingLuckyLoading, setFeelingLuckyLoading] = useState(false);
  
  const handleFeelingLucky = async () => {
    if (!team) {
      toast.error("Create a team first!");
      return;
    }
    
    if (team.celebrities?.length >= 10) {
      toast.error("Team is full! Remove a celebrity first.");
      return;
    }
    
    setFeelingLuckyLoading(true);
    try {
      // Get a random affordable celebrity
      const { celebrity } = await feelingLucky(team.id);
      
      if (celebrity) {
        // Add to team
        const result = await addToTeamAPI(team.id, celebrity.id);
        setTeam(result.team);
        
        if (result.brown_bread_bonus) {
          toast.success(`🎲 Lucky pick: ${celebrity.name} + 💀 Brown Bread Bonus!`, { duration: 5000 });
        } else {
          toast.success(`🎲 Lucky pick: ${celebrity.name} added for £${celebrity.price}M!`);
        }
        
        fetchLeaderboard();
        fetchTopPicked();
        fetchStats();
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "No luck this time! Try again.");
    } finally {
      setFeelingLuckyLoading(false);
    }
  };

  // Remove celebrity from team
  const removeFromTeam = async (celebrityId) => {
    if (!team) return;
    
    // Check if team is locked
    if (team.is_locked && !isTransferWindowOpen) {
      toast.error("Team is locked! Wait for transfer window (Sunday 12pm)");
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
      const response = await fetch(`${API}/team/submit`, {
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
      const response = await fetch(`${API}/transfer-window-status`);
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

  // Load team-related data when team changes
  useEffect(() => {
    if (team?.id) {
      fetchTeamLeaguesData(team.id);
      fetchPriceAlerts(team.id);
    }
    // Fetch hot streaks regardless of team
    fetchHotStreaks();
  }, [team?.id, fetchTeamLeaguesData, fetchPriceAlerts, fetchHotStreaks]);

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
      
      {/* Initial Layout Loading - Show minimal skeleton until JS hydration completes */}
      {!isLayoutReady && (
        <div className="fixed inset-0 bg-[#050505] z-[9999] flex items-center justify-center">
          <div className="text-center">
            <h1 className="font-anton text-4xl md:text-6xl text-white uppercase">
              <span className="text-[#FF0099]">Celebrity</span>
              <br />
              <span className="text-[#FFD700]">Buzz</span> <span className="text-[#00F0FF]">Index</span>
            </h1>
            <p className="text-[#A1A1AA] text-sm mt-4">Loading...</p>
          </div>
        </div>
      )}
      
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
        {/* How It Works - Collapsed by default with toggle button */}
        <div className="mb-4">
          <button
            onClick={() => setShowHowItWorks(!showHowItWorks)}
            className="flex items-center gap-2 mx-auto bg-[#1A1A1A] hover:bg-[#262626] border border-[#333] px-4 py-2 rounded-full transition-all"
            data-testid="how-it-works-toggle"
          >
            <Info className="w-4 h-4 text-[#FFD700]" />
            <span className="text-sm font-medium text-white">How It Works</span>
            {showHowItWorks ? (
              <ChevronUp className="w-4 h-4 text-[#A1A1AA]" />
            ) : (
              <ChevronDown className="w-4 h-4 text-[#A1A1AA]" />
            )}
          </button>
        </div>
        {showHowItWorks && (
          <HowItWorks onShowMethodology={() => setShowMethodology(true)} />
        )}
      </div>
      
      <HotCelebsBanner celebs={hotCelebs} onSelect={handleCelebSearch} onAdd={addFromHotCelebs} />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <SearchBar 
          onSearch={searchCelebrity} 
          onQuickAdd={quickAddFromSearch}
          loading={searchLoading} 
          team={team}
        />
        
        {/* Feeling Lucky Button */}
        <div className="flex justify-center mb-4">
          <button
            onClick={handleFeelingLucky}
            disabled={feelingLuckyLoading || !team || team.celebrities?.length >= 10}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#FF0099] to-[#FFD700] hover:from-[#e6008a] hover:to-[#e6c200] text-white font-bold rounded-full transition-all transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
            data-testid="feeling-lucky-btn"
          >
            <Dice6 className={`w-5 h-5 ${feelingLuckyLoading ? 'animate-spin' : ''}`} />
            {feelingLuckyLoading ? 'Rolling...' : "I'm Feeling Lucky!"}
          </button>
        </div>
        
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
                
                {/* Wikipedia Link */}
                {searchedCeleb.wiki_url && (
                  <a 
                    href={searchedCeleb.wiki_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-[#00F0FF] hover:text-[#00F0FF]/80 text-sm mb-4 transition-colors"
                    data-testid="wikipedia-link"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View on Wikipedia
                  </a>
                )}
                
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
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block bg-[#1A1A1A] p-3 rounded border border-[#262626] hover:border-[#FF0099] hover:bg-[#1A1A1A]/80 transition-all cursor-pointer group"
                            data-testid={`news-article-${idx}`}
                          >
                            <p className="text-white text-sm font-medium mb-1 line-clamp-2 group-hover:text-[#FF0099] transition-colors">{article.title}</p>
                            <div className="flex items-center justify-between text-xs">
                              <span className="text-[#A1A1AA]">
                                {article.source}
                              </span>
                              <span className="text-[#666]">{article.date}</span>
                            </div>
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
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4">
              {[1, 2, 3, 4].map(i => <LoadingCard key={i} />)}
            </div>
          ) : celebrities.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 md:gap-4" data-testid="celebrity-grid">
              {(isMobile ? celebrities.slice(0, 6) : celebrities).map((celeb, idx) => (
                <CelebrityCard
                  key={celeb.id || `celeb-${idx}`}
                  celebrity={celeb}
                  onAdd={addToTeam}
                  onRemove={removeFromTeam}
                  isInTeam={isInTeam(celeb.id)}
                  canAfford={canAfford(celeb.price)}
                  onShowPriceHistory={handleShowPriceHistory}
                  compact={isMobile}
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
          <HotStreaks streaks={hotStreaks} onCelebClick={searchCelebrity} onAdd={addFromHotCelebs} />
        </div>
        
        {/* Brown Bread, Most Picked, Leaderboard */}
        <div className="mt-6 md:mt-8">
          {/* Desktop: Show all in grid */}
          <div className="hidden md:grid grid-cols-3 gap-6">
            <BrownBreadWatch watchList={brownBreadWatch} onSelect={searchCelebrity} onAdd={addFromHotCelebs} />
            <TopPickedCelebs celebs={topPicked} onSelect={searchCelebrity} onAdd={addFromHotCelebs} />
            <Leaderboard entries={leaderboard} />
          </div>
          
          {/* Mobile: Collapsible tabs */}
          <div className="md:hidden space-y-3">
            {/* Brown Bread Watch Tab */}
            <div className="bg-[#0A0A0A] border border-[#262626] rounded-lg overflow-hidden">
              <button
                onClick={() => setMobileExpandedTab(mobileExpandedTab === 'brownbread' ? null : 'brownbread')}
                className="w-full flex items-center justify-between p-4 text-left"
                data-testid="mobile-brownbread-tab"
              >
                <span className="flex items-center gap-2 font-bold text-white">
                  <span className="text-xl">💀</span> Brown Bread Watch
                  <span className="text-xs bg-[#FF0099] px-2 py-0.5 rounded-full">{brownBreadWatch.length}</span>
                </span>
                {mobileExpandedTab === 'brownbread' ? (
                  <ChevronUp className="w-5 h-5 text-[#FF0099]" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-[#A1A1AA]" />
                )}
              </button>
              {mobileExpandedTab === 'brownbread' && (
                <div className="border-t border-[#262626]">
                  <BrownBreadWatch watchList={brownBreadWatch} onSelect={searchCelebrity} onAdd={addFromHotCelebs} />
                </div>
              )}
            </div>
            
            {/* Most Picked Tab */}
            <div className="bg-[#0A0A0A] border border-[#262626] rounded-lg overflow-hidden">
              <button
                onClick={() => setMobileExpandedTab(mobileExpandedTab === 'mostpicked' ? null : 'mostpicked')}
                className="w-full flex items-center justify-between p-4 text-left"
                data-testid="mobile-mostpicked-tab"
              >
                <span className="flex items-center gap-2 font-bold text-white">
                  <span className="text-xl">🔥</span> Most Picked
                  <span className="text-xs bg-[#FFD700] text-black px-2 py-0.5 rounded-full">{topPicked.length}</span>
                </span>
                {mobileExpandedTab === 'mostpicked' ? (
                  <ChevronUp className="w-5 h-5 text-[#FFD700]" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-[#A1A1AA]" />
                )}
              </button>
              {mobileExpandedTab === 'mostpicked' && (
                <div className="border-t border-[#262626]">
                  <TopPickedCelebs celebs={topPicked.slice(0, 5)} onSelect={searchCelebrity} onAdd={addFromHotCelebs} />
                </div>
              )}
            </div>
            
            {/* Leaderboard Tab */}
            <div className="bg-[#0A0A0A] border border-[#262626] rounded-lg overflow-hidden">
              <button
                onClick={() => setMobileExpandedTab(mobileExpandedTab === 'leaderboard' ? null : 'leaderboard')}
                className="w-full flex items-center justify-between p-4 text-left"
                data-testid="mobile-leaderboard-tab"
              >
                <span className="flex items-center gap-2 font-bold text-white">
                  <span className="text-xl">🏆</span> Leaderboard
                  <span className="text-xs bg-[#00D4FF] text-black px-2 py-0.5 rounded-full">{leaderboard.length}</span>
                </span>
                {mobileExpandedTab === 'leaderboard' ? (
                  <ChevronUp className="w-5 h-5 text-[#00D4FF]" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-[#A1A1AA]" />
                )}
              </button>
              {mobileExpandedTab === 'leaderboard' && (
                <div className="border-t border-[#262626]">
                  <Leaderboard entries={leaderboard} />
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Friends Leagues and Sidebar - Hidden on mobile for cleaner layout */}
        <div className={`${isMobile ? 'hidden' : 'grid'} grid-cols-1 lg:grid-cols-12 gap-8 mt-8`}>
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
            
            {/* Price Watch Button */}
            <button
              onClick={() => setShowPriceWatch(true)}
              className="w-full bg-gradient-to-r from-[#FF0099] to-[#7B2CFF] text-white font-bold py-3 px-4 flex items-center justify-center gap-2 hover:from-[#FF33AD] hover:to-[#9456FF] transition-all"
              data-testid="price-watch-btn"
            >
              <span className="text-xl">👁️</span>
              Price Watch
            </button>
            
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
        
        {/* Mobile-only Quick Actions */}
        {isMobile && (
          <div className="mt-6 grid grid-cols-2 gap-3">
            <button
              onClick={() => setShowPriceWatch(true)}
              className="bg-gradient-to-r from-[#FF0099] to-[#7B2CFF] text-white font-bold py-3 px-3 flex items-center justify-center gap-2 rounded-lg text-sm"
              data-testid="price-watch-btn-mobile"
            >
              👁️ Price Watch
            </button>
            <button
              onClick={() => { fetchHallOfFameData(); setShowHallOfFame(true); }}
              className="bg-gradient-to-r from-[#FFD700] to-[#FF8C00] text-black font-bold py-3 px-3 flex items-center justify-center gap-2 rounded-lg text-sm"
              data-testid="hall-of-fame-btn-mobile"
            >
              🏆 Hall of Fame
            </button>
          </div>
        )}
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
      
      {/* Price Watch Modal */}
      {showPriceWatch && team && (
        <PriceWatch 
          teamId={team.id}
          onClose={() => setShowPriceWatch(false)}
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
          apiUrl={API_URL}
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
      
      {/* FAQ Section */}
      <section className="bg-[#0D0D0D] py-12 px-4" data-testid="faq-section">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-8 text-center">
            Frequently Asked Questions
          </h2>
          
          <div className="space-y-4">
            {/* FAQ Item 1 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                How do points work?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-3">
                <p>Points are earned based on your celebrities' <strong className="text-white">real news coverage</strong>. Every time one of your celebs appears in the headlines, you score!</p>
                
                <div className="bg-[#0D0D0D] p-3 rounded border border-[#333]">
                  <p className="text-white font-bold mb-2">Point Scoring:</p>
                  <ul className="list-disc list-inside space-y-1 ml-1">
                    <li>Each news article = base points</li>
                    <li><span className="text-red-400 font-bold">Scandal/Controversy bonus!</span> Negative news earns extra points (arrests, feuds, lawsuits = big points)</li>
                  </ul>
                  
                  <p className="text-white font-bold mb-2 mt-4">Search Icons:</p>
                  <ul className="list-disc list-inside space-y-1 ml-1">
                    <li><span className="text-cyan-400">🌍 Number</span> = Wikipedia languages - celebrities with higher numbers are more internationally recognized</li>
                  </ul>
                </div>
                
                <p><strong className="text-[#00F0FF]">Auto-updates:</strong> Points recalculate automatically as new articles are published throughout the day.</p>
              </div>
            </details>
            
            {/* FAQ Item 2 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                How are scandals detected?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>We scan news headlines for <strong className="text-white">scandal keywords</strong> like arrest, scandal, lawsuit, feud, divorce, rehab, or controversy.</p>
                <p>Scandal news = bonus points! A celebrity embroiled in controversy will shoot up the leaderboard.</p>
              </div>
            </details>
            
            {/* FAQ Item 3 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                How does celebrity pricing work?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>Celebrities are priced based on their <strong className="text-white">tier</strong> and <strong className="text-white">current buzz</strong>:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li><strong className="text-[#FFD700]">A-LIST:</strong> £10M - £15M (mega stars at the top)</li>
                  <li><strong className="text-[#C0C0C0]">B-LIST:</strong> £4M - £6.9M</li>
                  <li><strong className="text-[#CD7F32]">C-LIST:</strong> £1.5M - £2.9M</li>
                  <li><strong className="text-[#666]">D-LIST:</strong> £0.5M - £1M</li>
                </ul>
                <p className="mt-2"><strong className="text-[#00F0FF]">Price changes affect transfers!</strong> When you transfer a celebrity out, you get their <em>current</em> market value. If their price went up, you profit. If it dropped, you lose money. Buy low, transfer high!</p>
              </div>
            </details>
            
            {/* FAQ Item 4 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                How are celebrity tiers decided?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p className="text-[#FF0099] italic">"But my favourite celeb should be A-List!" - Sorry mate, the algorithm doesn't care about your feelings. 🤷</p>
                <p>Tiers are determined by our <strong className="text-white">Global Recognition Algorithm</strong> which considers:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li><strong className="text-[#00F0FF]">🌍 Wikipedia Languages:</strong> The main factor - how many language editions feature the celebrity (shown as the number next to 🌍)</li>
                  <li><strong className="text-[#FFD700]">Major Awards:</strong> Oscar, Grammy, Emmy winners get tier upgrades</li>
                  <li><strong className="text-[#FF0099]">Franchise Leads:</strong> Stars of Harry Potter, Marvel, Star Wars etc. get A-List status</li>
                  <li><strong className="text-white">World Champions:</strong> Olympic gold medalists, world record holders</li>
                </ul>
                <p className="mt-2 text-xs">
                  <strong className="text-[#FFD700]">A-LIST:</strong> 60+ languages | 
                  <strong className="text-[#C0C0C0]"> B-LIST:</strong> 25-59 | 
                  <strong className="text-[#CD7F32]"> C-LIST:</strong> 10-24 | 
                  <strong className="text-[#666]"> D-LIST:</strong> &lt;10
                </p>
                <p className="text-xs text-[#666] mt-2 italic">The Wikipedia community has spoken. Take it up with them, not us! 😏</p>
              </div>
            </details>
            
            {/* FAQ Item 5 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                When can I make transfers?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>The <strong className="text-white">Transfer Window</strong> opens every <strong className="text-[#00F0FF]">Sunday at 12pm GMT</strong> and stays open until midnight.</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>You get <strong className="text-white">3 transfers</strong> per week</li>
                  <li>Submit your team to lock it in before the window closes</li>
                  <li>Unused transfers don't carry over</li>
                </ul>
              </div>
            </details>
            
            {/* FAQ Item 6 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                What is the Brown Bread Watch?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>The <strong className="text-white">Brown Bread Watch</strong> 💀 tracks elderly celebrities (80+) who may... shuffle off this mortal coil.</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>They receive a <strong className="text-white">Brown Bread Bonus</strong> - extra points!</li>
                  <li>A morbid but strategic consideration for your team...</li>
                </ul>
              </div>
            </details>
            
            {/* FAQ Item 7 */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                How do I save my team?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>Sign in with <strong className="text-white">Google</strong> to save your team permanently!</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Guest teams are saved locally but may be lost if you clear your browser</li>
                  <li>Signing in links your team to your account forever</li>
                  <li>Create or join <strong className="text-white">Friends Leagues</strong> to compete with mates</li>
                </ul>
              </div>
            </details>
            
            {/* FAQ Item 8 - Deceased Celebrities */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                Why are deceased celebrities still in the game? 💀
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>Because scandals can <strong className="text-white">come from the grave!</strong> 🪦</p>
                <p>Think about it - posthumous albums, unreleased footage, estate drama, documentary revelations... dead celebs can still hit the headlines!</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>💀 <strong className="text-white">Brown Bread Bonus</strong>: +100 points if a celeb in your team passes away</li>
                  <li>📰 Legacy news still counts towards buzz points</li>
                  <li>🎬 Documentaries and tributes = headline gold</li>
                </ul>
                <p className="text-[#FFD700] font-bold mt-2">The ultimate long-term investment strategy? 👀</p>
              </div>
            </details>
            
            {/* FAQ Item 9 - News Sources */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                Where does the news come from? 📰
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>We scour <strong className="text-[#FFD700]">58+ major news sources</strong> plus <strong className="text-[#00F0FF]">Google Trends</strong> across the UK and US! 🌍</p>
                <p className="font-bold text-white">UK Sources (27):</p>
                <p className="text-xs">Daily Mail, The Sun, Daily Mirror, Metro, Express, BBC News, The Guardian, The Independent, OK! Magazine, Hello!, Sky News, Digital Spy, Radio Times, Closer, Glamour UK, Cosmopolitan UK, Evening Standard, Daily Star, Daily Record, The Telegraph, ITV News, Heat Magazine, Grazia UK, Marie Claire UK, Manchester Evening News, Liverpool Echo, NME</p>
                <p className="font-bold text-white mt-2">US Sources (28):</p>
                <p className="text-xs">TMZ, People, Us Weekly, Page Six, E! News, Entertainment Tonight, Just Jared, BuzzFeed, HuffPost, Yahoo News, National Enquirer, Access Hollywood, Extra TV, Inside Edition, Daily Beast, Vulture, Refinery29, Variety, Hollywood Reporter, Deadline, Vanity Fair, Billboard, Rolling Stone, Pitchfork, CNN, Fox News, CBS News, ABC News</p>
                <p className="font-bold text-white mt-2">Trending Data:</p>
                <p className="text-xs">📈 <strong className="text-[#00F0FF]">Google Trends</strong> - Real-time trending searches from UK & US to spot rising celebrities</p>
                <p className="text-[#00F0FF] font-bold mt-2">Every headline and trending search counts towards your team's buzz score! 🔥</p>
              </div>
            </details>
            
            {/* FAQ Item 10 - Beta Notice */}
            <details className="bg-[#1A1A1A] rounded-lg border border-[#262626] group">
              <summary className="flex justify-between items-center p-4 cursor-pointer text-white font-medium hover:text-[#FF0099] transition-colors">
                Why is [celebrity] in the wrong category or priced weirdly?
                <span className="text-[#FF0099] group-open:rotate-180 transition-transform">▼</span>
              </summary>
              <div className="px-4 pb-4 text-[#A1A1AA] text-sm space-y-2">
                <p>We're in <strong className="text-[#FFD700]">BETA</strong> mate! 🚧</p>
                <p>Our algorithm pulls data from Wikipedia and news sources, but sometimes it gets a bit confused. If you spot a well-known celeb priced at £0.5M or in a bizarre category...</p>
                <p className="text-[#00F0FF] font-bold">SNAP THEM UP! 💰</p>
                <p>Seriously, it's not that deep. Take advantage of the bargains while they last. We're working on it, but in the meantime, enjoy the chaos and build your team on the cheap!</p>
                <p className="text-xs text-[#666] mt-2 italic">*Prices and categories may update at any time. No refunds for shrewd investments. 😉</p>
              </div>
            </details>
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <Footer playerCount={stats?.player_count} onTermsClick={() => setShowTerms(true)} />
      
      {/* Terms Modal */}
      {showTerms && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0A0A0A] border border-[#262626] rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="font-anton text-2xl uppercase">
                  <span className="text-[#FF0099]">Terms</span> & <span className="text-[#00F0FF]">Conditions</span>
                </h2>
                <button 
                  onClick={() => setShowTerms(false)}
                  className="text-[#A1A1AA] hover:text-white p-2"
                  data-testid="close-terms"
                >
                  <X size={24} />
                </button>
              </div>
              
              <div className="space-y-6 text-[#E5E5E5]">
                <section>
                  <h3 className="text-lg font-bold text-white mb-2">Data Sources</h3>
                  <p>Data displayed on this platform is derived from publicly available sources including Wikipedia and other open data repositories.</p>
                </section>
                
                <section>
                  <h3 className="text-lg font-bold text-white mb-2">Rankings</h3>
                  <p>All celebrity rankings and tier classifications are algorithmically generated based on publicly available metrics. These rankings are for entertainment purposes only.</p>
                </section>
                
                <section>
                  <h3 className="text-lg font-bold text-white mb-2">Trademarks</h3>
                  <p>All trademarks, service marks, trade names, and logos displayed on this platform belong to their respective owners.</p>
                </section>
              </div>
              
              <div className="mt-6 pt-4 border-t border-[#262626]">
                <button 
                  onClick={() => setShowTerms(false)}
                  className="w-full bg-[#FF0099] hover:bg-[#FF0099]/80 text-white py-2 rounded transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
