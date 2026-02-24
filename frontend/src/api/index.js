import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;
export const AUTH_API = `${BACKEND_URL}/api/auth`;

// Configure axios to include credentials for all requests
axios.defaults.withCredentials = true;

// Category Icons mapping
export const categoryIcons = {
  movie_stars: "Film",
  tv_actors: "Tv",
  musicians: "Music",
  athletes: "Trophy",
  royals: "Crown",
  reality_tv: "Star",
  other: "Users",
};

// Tier colors configuration
export const tierColors = {
  A: { bg: "bg-[#FFD700]", text: "text-black", label: "A-LIST" },
  B: { bg: "bg-[#C0C0C0]", text: "text-black", label: "B-LIST" },
  C: { bg: "bg-[#CD7F32]", text: "text-white", label: "C-LIST" },
  D: { bg: "bg-[#666666]", text: "text-white", label: "D-LIST" },
};

// API Functions
export const fetchCategories = async () => {
  const res = await axios.get(`${API}/categories`);
  return res.data.categories || [];
};

export const fetchTrending = async () => {
  const res = await axios.get(`${API}/trending`);
  return res.data.trending || [];
};

export const fetchCelebritiesByCategory = async (category) => {
  // Strong cache busting - random number + timestamp ensures no caching
  const cacheBuster = `${Date.now()}_${Math.random()}`;
  const res = await axios.get(`${API}/celebrities/category/${category}?_nocache=${cacheBuster}`);
  return res.data.celebrities || [];
};

export const searchCelebrityAPI = async (name) => {
  const res = await axios.post(`${API}/celebrity/search`, { name });
  return res.data.celebrity;
};

export const fetchAutocomplete = async (query) => {
  const res = await axios.get(`${API}/autocomplete?q=${encodeURIComponent(query)}`);
  return res.data.suggestions || [];
};

export const fetchStats = async () => {
  const res = await axios.get(`${API}/stats`);
  return res.data;
};

export const fetchTodaysNews = async () => {
  const res = await axios.get(`${API}/todays-news`);
  return res.data.news || [];
};

export const fetchTopPicked = async () => {
  const res = await axios.get(`${API}/top-picked`);
  return res.data.top_picked || [];
};

export const fetchHotCelebs = async () => {
  const res = await axios.get(`${API}/hot-celebs`);
  return res.data.hot_celebs || [];
};

export const fetchBrownBreadWatch = async () => {
  const res = await axios.get(`${API}/brown-bread-watch`);
  return res.data.watch_list || [];
};

export const fetchPriceAlerts = async (teamId) => {
  const res = await axios.get(`${API}/price-alerts/${teamId}`);
  return res.data.alerts || [];
};

export const fetchHotStreaks = async () => {
  const res = await axios.get(`${API}/hot-streaks`);
  return res.data.hot_streaks || [];
};

export const fetchPriceHistory = async (celebrityName) => {
  const res = await axios.get(`${API}/price-history/celebrity-name/${encodeURIComponent(celebrityName)}`);
  return res.data;
};

export const generateAiImage = async (name, description = "") => {
  const res = await axios.post(`${API}/celebrity/generate-image`, { name, description });
  return res.data;
};

export const getAiImage = async (name) => {
  const res = await axios.get(`${API}/celebrity/ai-image/${encodeURIComponent(name)}`);
  return res.data;
};

export const fetchLeaderboard = async () => {
  const res = await axios.get(`${API}/leaderboard`);
  return res.data.leaderboard || [];
};

export const fetchHallOfFame = async () => {
  const res = await axios.get(`${API}/hall-of-fame`);
  return res.data.hall_of_fame || [];
};

export const fetchCustomOptions = async () => {
  const res = await axios.get(`${API}/team/customization-options`);
  return res.data;
};

// Team API
export const createTeam = async (teamName) => {
  const res = await axios.post(`${API}/team/create`, { team_name: teamName });
  return res.data.team;
};

export const getTeam = async (teamId) => {
  const res = await axios.get(`${API}/team/${teamId}`);
  return res.data.team;
};

export const addToTeamAPI = async (teamId, celebrityId) => {
  const res = await axios.post(`${API}/team/add`, {
    team_id: teamId,
    celebrity_id: celebrityId
  });
  return res.data;
};

export const removeFromTeamAPI = async (teamId, celebrityId) => {
  const res = await axios.post(`${API}/team/remove`, {
    team_id: teamId,
    celebrity_id: celebrityId
  });
  return res.data.team;
};

export const customizeTeamAPI = async (teamId, teamName, teamColor, teamIcon) => {
  const res = await axios.post(`${API}/team/customize`, {
    team_id: teamId,
    team_name: teamName || undefined,
    team_color: teamColor || undefined,
    team_icon: teamIcon || undefined
  });
  return res.data.team;
};

export const fetchTeamLeagues = async (teamId) => {
  const res = await axios.get(`${API}/team/${teamId}/leagues`);
  return res.data.leagues || [];
};

// League API
export const createLeagueAPI = async (name, teamId) => {
  const res = await axios.post(`${API}/league/create`, { name, team_id: teamId });
  return res.data.league;
};

export const joinLeagueAPI = async (code, teamId) => {
  const res = await axios.post(`${API}/league/join`, { code, team_id: teamId });
  return res.data;
};

export const fetchLeagueLeaderboard = async (leagueId) => {
  const res = await axios.get(`${API}/league/${leagueId}/leaderboard`);
  return res.data.leaderboard || [];
};

// Auth API
export const checkAuthStatus = async () => {
  const res = await axios.get(`${AUTH_API}/me`);
  return res.data;
};

export const exchangeSession = async (sessionId) => {
  const res = await axios.post(`${AUTH_API}/session`, { session_id: sessionId });
  return res.data;
};

export const logoutAPI = async () => {
  await axios.post(`${AUTH_API}/logout`);
};

export const sendMagicLink = async (email) => {
  const res = await axios.post(`${AUTH_API}/magic-link/send`, { email });
  return res.data;
};

export const verifyMagicLink = async (token) => {
  const res = await axios.post(`${AUTH_API}/magic-link/verify`, { token });
  return res.data;
};

// Price Watch API
export const getPriceWatches = async (teamId) => {
  const res = await axios.get(`${API}/price-watch/${teamId}`);
  return res.data.watches || [];
};

export const createPriceWatch = async (teamId, celebrityName, targetPrice, alertType = "below") => {
  const res = await axios.post(`${API}/price-watch/${teamId}`, {
    celebrity_name: celebrityName,
    target_price: targetPrice,
    alert_type: alertType
  });
  return res.data;
};

export const deletePriceWatch = async (teamId, watchId) => {
  const res = await axios.delete(`${API}/price-watch/${teamId}/${watchId}`);
  return res.data;
};

export const getTriggeredWatches = async (teamId) => {
  const res = await axios.get(`${API}/price-watch/${teamId}/triggered`);
  return res.data;
};
