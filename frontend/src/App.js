import { useEffect, useState, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Search, Crown, Film, Tv, Music, Trophy, Star, Share2, X, Copy, Check, TrendingUp, TrendingDown, Minus, Plus, Users, Info, ChevronUp, Newspaper, ArrowLeftRight, Skull, Facebook, UserPlus, Home, Clock, Bell, LineChart } from "lucide-react";

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
  
  const transferWindow = stats.transfer_window || {};
  const isOpen = transferWindow.is_open;
  const statusText = transferWindow.status || "Loading...";
  
  return (
    <div className="bg-gradient-to-r from-[#FF0099]/10 via-[#0A0A0A] to-[#00F0FF]/10 border border-[#262626] p-4 mb-6">
      <div className="flex flex-wrap items-center justify-center gap-4 md:gap-8 text-center">
        <span className="flex items-center gap-2">
          <Users className="w-4 h-4 text-[#FF0099]" />
          <span className="text-[#A1A1AA]">Players:</span>
          <span className="text-[#FFD700] font-bold">{stats.player_count?.toLocaleString() || 0}</span>
        </span>
        <span className={`flex items-center gap-2 px-3 py-1 ${isOpen ? 'bg-green-500/20 border border-green-500' : 'bg-[#262626]'}`}>
          <Clock className="w-4 h-4 text-[#00F0FF]" />
          <span className="text-[#A1A1AA]">Transfer Window:</span>
          <span className={`font-bold ${isOpen ? 'text-green-400' : 'text-[#00F0FF]'}`}>{statusText}</span>
        </span>
      </div>
    </div>
  );
};

// Transfer Window Banner with Live Countdown
const TransferWindowBanner = ({ stats }) => {
  const [countdown, setCountdown] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  
  useEffect(() => {
    if (!stats?.transfer_window) return;
    
    const updateCountdown = () => {
      const now = new Date();
      const transferWindow = stats.transfer_window;
      
      // Calculate if window is open (Saturday 12pm GMT to Sunday 12pm GMT)
      const utcDay = now.getUTCDay();
      const utcHour = now.getUTCHours();
      const utcMinutes = now.getUTCMinutes();
      const utcSeconds = now.getUTCSeconds();
      
      // Window is open: Saturday (6) from 12:00 to Sunday (0) 12:00 UTC
      const windowOpen = (utcDay === 6 && utcHour >= 12) || (utcDay === 0 && utcHour < 12);
      setIsOpen(windowOpen);
      
      if (windowOpen) {
        // Calculate time remaining until Sunday 12pm GMT
        let hoursLeft, minsLeft, secsLeft;
        if (utcDay === 6) {
          // Saturday after 12pm - hours until midnight + 12 hours Sunday
          hoursLeft = (23 - utcHour) + 12;
          minsLeft = 59 - utcMinutes;
          secsLeft = 59 - utcSeconds;
        } else {
          // Sunday before 12pm
          hoursLeft = 11 - utcHour;
          minsLeft = 59 - utcMinutes;
          secsLeft = 59 - utcSeconds;
        }
        setCountdown(`${hoursLeft}h ${minsLeft}m ${secsLeft}s remaining`);
      } else {
        // Calculate time until next Saturday 12pm GMT
        let daysUntil = (6 - utcDay + 7) % 7;
        if (daysUntil === 0 && utcHour >= 12) {
          daysUntil = 7;
        }
        
        // Calculate exact time until Saturday 12:00 GMT
        const nextSaturday = new Date(now);
        nextSaturday.setUTCDate(now.getUTCDate() + daysUntil);
        nextSaturday.setUTCHours(12, 0, 0, 0);
        
        const diff = nextSaturday - now;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const secs = Math.floor((diff % (1000 * 60)) / 1000);
        
        if (days > 0) {
          setCountdown(`${days}d ${hours}h ${mins}m ${secs}s`);
        } else {
          setCountdown(`${hours}h ${mins}m ${secs}s`);
        }
      }
    };
    
    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [stats]);
  
  if (!stats) return null;
  
  return (
    <div className={`${isOpen 
      ? 'bg-gradient-to-r from-green-500/20 via-green-500/10 to-green-500/20 border-green-500' 
      : 'bg-gradient-to-r from-[#FF0099]/10 via-[#0A0A0A] to-[#00F0FF]/10 border-[#262626]'
    } border p-2 sm:p-3 text-center`} data-testid="transfer-window-banner">
      <div className="flex items-center justify-center gap-2 sm:gap-3 flex-wrap">
        <Clock className={`w-4 h-4 sm:w-5 sm:h-5 ${isOpen ? 'text-green-400 animate-pulse' : 'text-[#00F0FF]'}`} />
        <span className="text-[#A1A1AA] font-medium text-xs sm:text-sm">Transfer Window:</span>
        {isOpen ? (
          <span className="text-green-400 font-bold animate-pulse text-xs sm:text-sm">
            🟢 OPEN - {countdown}
          </span>
        ) : (
          <span className="text-[#00F0FF] font-bold text-xs sm:text-sm">
            Opens in {countdown}
          </span>
        )}
      </div>
      <p className="text-[10px] sm:text-xs text-[#A1A1AA]/70 mt-1">
        {isOpen 
          ? "Make up to 2 transfers now! Window closes Sunday 12pm GMT" 
          : "2 transfers allowed per window • Every Saturday 12pm - Sunday 12pm GMT"
        }
      </p>
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
        
        <h4 className="font-bold text-white mb-3">Tier Pricing (Dynamic)</h4>
        <div className="space-y-2 mb-6">
          <div className="bg-[#FFD700] text-black p-2 flex justify-between items-center">
            <span className="font-bold">A-LIST</span>
            <span className="text-sm">£9m-£12m • High scoring but expensive</span>
          </div>
          <div className="bg-[#C0C0C0] text-black p-2 flex justify-between items-center">
            <span className="font-bold">B-LIST</span>
            <span className="text-sm">£5m-£8m • Balanced steady picks</span>
          </div>
          <div className="bg-[#CD7F32] text-white p-2 flex justify-between items-center">
            <span className="font-bold">C-LIST</span>
            <span className="text-sm">£2m-£4m • Risk/reward</span>
          </div>
          <div className="bg-[#666666] text-white p-2 flex justify-between items-center">
            <span className="font-bold">D-LIST</span>
            <span className="text-sm">£0.5m-£1.5m • Cheap wildcards</span>
          </div>
        </div>
        
        <div className="bg-[#00F0FF]/10 border border-[#00F0FF] p-4 mb-4">
          <h4 className="font-bold text-[#00F0FF] mb-2">📈 Dynamic Pricing</h4>
          <p className="text-sm text-[#A1A1AA]">Prices fluctuate weekly based on media coverage. Hot celebs cost more, quiet celebs cost less!</p>
        </div>
        
        <div className="bg-[#FF0099]/20 border border-[#FF0099] p-4 mb-4">
          <h4 className="font-bold text-[#FF0099] mb-2">🕐 Transfer Window</h4>
          <p className="text-sm text-[#A1A1AA]">Opens every <span className="text-white font-bold">Saturday at 12pm GMT</span> for 24 hours. Make your moves!</p>
        </div>
        
        <h4 className="font-bold text-white mb-3">Points Multipliers</h4>
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

// Today's News Component - Compact 6 items
const TodaysNews = ({ news }) => {
  if (!news || news.length === 0) return null;
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="todays-news">
      <h3 className="font-anton text-lg uppercase tracking-tight text-[#FF0099] mb-3 flex items-center gap-2">
        <Newspaper className="w-5 h-5" />
        Celeb News
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {news.slice(0, 6).map((item, idx) => (
          <a 
            key={idx} 
            href={item.url || "#"} 
            target="_blank" 
            rel="noopener noreferrer"
            className="bg-[#1A1A1A] p-2 hover:bg-[#222] transition-colors block group"
          >
            <p className="text-[10px] text-[#00F0FF] uppercase mb-1">{item.source}</p>
            <p className="font-bold text-xs text-white line-clamp-3 group-hover:text-[#FF0099]">{item.headline}</p>
          </a>
        ))}
      </div>
    </div>
  );
};

// Hot Celebs This Week Banner Component - Auto-scrolling
const HotCelebsBanner = ({ celebs, onSelect }) => {
  if (!celebs || celebs.length === 0) return null;
  
  // Double the celebs for infinite scroll effect
  const doubledCelebs = [...celebs, ...celebs];
  
  return (
    <div className="bg-gradient-to-r from-[#FF0099]/30 via-[#0A0A0A] to-[#00F0FF]/30 border-b border-[#FF0099]/50 p-4 overflow-hidden" data-testid="hot-celebs-banner">
      <div className="max-w-7xl mx-auto">
        <h3 className="font-anton text-lg uppercase tracking-tight text-white mb-3 flex items-center gap-2">
          🔥 Hot Celebs This Week
          <span className="text-xs font-normal text-[#A1A1AA]">(prices increase with news coverage)</span>
        </h3>
        <div className="hot-celebs-scroll-container">
          <div className="hot-celebs-scroll-content">
            {doubledCelebs.map((celeb, idx) => (
              <div 
                key={idx}
                onClick={() => onSelect(celeb.name)}
                className="flex-shrink-0 w-28 bg-[#1A1A1A] border border-[#262626] p-2 cursor-pointer hover:border-[#FF0099] transition-colors group"
              >
                <div className="relative mb-1">
                  <img 
                    src={celeb.image} 
                    alt={celeb.name}
                    className="w-full h-20 object-cover"
                    onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=128&background=FF0099&color=fff`; }}
                  />
                  <div className={`absolute top-0 right-0 px-1 py-0.5 text-[7px] font-bold ${
                    celeb.tier === 'A' ? 'bg-[#FFD700] text-black' : celeb.tier === 'B' ? 'bg-[#C0C0C0] text-black' : celeb.tier === 'C' ? 'bg-[#CD7F32] text-white' : 'bg-[#666] text-white'
                  }`}>
                    {celeb.tier}-LIST
                  </div>
                  {celeb.trending_tag && (
                    <div className="absolute top-0 left-0 text-[10px]">
                      {celeb.trending_tag}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <p className="font-bold text-xs text-white truncate group-hover:text-[#FF0099] flex-1">{celeb.name}</p>
                  {celeb.news_premium && (
                    <TrendingUp className="w-3 h-3 text-[#00FF00] flex-shrink-0" />
                  )}
                </div>
                <p className={`text-[10px] font-bold ${celeb.news_premium ? 'text-[#00FF00]' : 'text-[#00FF00]'}`}>
                  £{celeb.price}M
                  {celeb.news_premium && <span className="text-[8px] ml-1 text-[#00FF00]">▲</span>}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Price History Modal Component
const PriceHistoryModal = ({ celebrityName, onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [currentTier, setCurrentTier] = useState("D");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${API}/price-history/celebrity-name/${encodeURIComponent(celebrityName)}`);
        setHistory(response.data.history || []);
        setCurrentPrice(response.data.current_price || 0);
        setCurrentTier(response.data.current_tier || "D");
      } catch (error) {
        console.error("Error fetching price history:", error);
        toast.error("Could not load price history");
      } finally {
        setLoading(false);
      }
    };
    
    if (celebrityName) {
      fetchHistory();
    }
  }, [celebrityName]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
  };

  const getPriceChange = (index) => {
    if (index >= history.length - 1) return null;
    const current = history[index].price;
    const previous = history[index + 1].price;
    const change = current - previous;
    return change;
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="price-history-modal">
      <div className="bg-[#0A0A0A] border border-[#262626] max-w-md w-full max-h-[80vh] overflow-hidden">
        <div className="p-4 border-b border-[#262626] flex justify-between items-center">
          <div>
            <h2 className="font-anton text-xl uppercase text-white flex items-center gap-2">
              <LineChart className="w-5 h-5 text-[#00F0FF]" />
              Price History
            </h2>
            <p className="text-sm text-[#A1A1AA]">{celebrityName}</p>
          </div>
          <button onClick={onClose} className="text-[#666] hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        <div className="p-4">
          <div className="bg-[#1A1A1A] p-4 mb-4 border border-[#262626]">
            <p className="text-sm text-[#A1A1AA]">Current Price</p>
            <p className="font-anton text-3xl text-[#00FF00]">£{currentPrice}M</p>
            <p className="text-xs text-[#FFD700]">{currentTier}-LIST</p>
          </div>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin w-8 h-8 border-2 border-[#FF0099] border-t-transparent rounded-full mx-auto"></div>
              <p className="text-sm text-[#A1A1AA] mt-2">Loading history...</p>
            </div>
          ) : history.length === 0 ? (
            <p className="text-center text-[#A1A1AA] py-8">No price history available yet</p>
          ) : (
            <div className="max-h-[300px] overflow-y-auto space-y-2">
              {history.map((entry, idx) => {
                const change = getPriceChange(idx);
                return (
                  <div key={idx} className="bg-[#1A1A1A] p-3 border border-[#262626] flex justify-between items-center">
                    <div>
                      <p className="text-sm text-white">£{entry.price}M</p>
                      <p className="text-xs text-[#A1A1AA]">{formatDate(entry.recorded_at)}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-[#FFD700]">{entry.tier}-LIST</p>
                      {change !== null && (
                        <p className={`text-xs flex items-center gap-1 ${change > 0 ? 'text-[#00FF00]' : change < 0 ? 'text-[#FF4444]' : 'text-[#A1A1AA]'}`}>
                          {change > 0 ? <TrendingUp className="w-3 h-3" /> : change < 0 ? <TrendingDown className="w-3 h-3" /> : null}
                          {change > 0 ? '+' : ''}{change.toFixed(1)}M
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
        
        <div className="p-4 border-t border-[#262626]">
          <p className="text-xs text-[#666] text-center">
            Prices update based on media buzz and trending status
          </p>
        </div>
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

// Price Alerts Component - Shows upcoming price changes for team
const PriceAlerts = ({ alerts, teamId }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="price-alerts">
        <h4 className="font-anton text-lg uppercase tracking-tight text-[#FFD700] mb-3 flex items-center gap-2">
          <Bell className="w-5 h-5" />
          Price Alerts
        </h4>
        <p className="text-xs text-[#666] text-center py-4">No significant price changes expected for your team</p>
      </div>
    );
  }
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="price-alerts">
      <h4 className="font-anton text-lg uppercase tracking-tight text-[#FFD700] mb-3 flex items-center gap-2">
        <Bell className="w-5 h-5" />
        Price Alerts
      </h4>
      <p className="text-xs text-[#666] mb-3">Price changes at next transfer window</p>
      <div className="space-y-2">
        {alerts.slice(0, 5).map((alert, idx) => (
          <div 
            key={idx}
            className={`flex items-center gap-3 p-2 border-l-2 ${
              alert.alert_type === 'rising' ? 'border-green-500 bg-green-500/10' : 'border-red-500 bg-red-500/10'
            }`}
          >
            <img 
              src={alert.image} 
              alt={alert.name}
              className="w-8 h-8 rounded-full object-cover"
              onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${alert.name}&size=32&background=FF0099&color=fff`; }}
            />
            <div className="flex-1 min-w-0">
              <span className="text-sm truncate block font-bold">{alert.name}</span>
              <span className="text-xs text-[#A1A1AA]">{alert.reason}</span>
            </div>
            <div className="text-right">
              <div className={`text-sm font-bold ${alert.alert_type === 'rising' ? 'text-green-400' : 'text-red-400'}`}>
                {alert.alert_type === 'rising' ? '↑' : '↓'} £{Math.abs(alert.change)}M
              </div>
              <div className="text-xs text-[#666]">
                £{alert.current_price}M → £{alert.projected_price}M
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Hot Streaks Component - Shows celebrities on fire in the news
const HotStreaks = ({ streaks, teamId }) => {
  if (!streaks || streaks.length === 0) {
    return null; // Don't show anything if no hot streaks
  }
  
  return (
    <div className="bg-gradient-to-r from-orange-500/10 via-[#0A0A0A] to-red-500/10 border border-orange-500/50 p-4 mb-4" data-testid="hot-streaks">
      <h4 className="font-anton text-lg uppercase tracking-tight text-orange-400 mb-3 flex items-center gap-2">
        🔥 Hot Streaks
      </h4>
      <p className="text-xs text-[#666] mb-3">Celebrities making headlines 3+ days in a row!</p>
      <div className="space-y-2">
        {streaks.slice(0, 5).map((streak, idx) => (
          <div 
            key={idx}
            className="flex items-center gap-3 p-2 bg-orange-500/5 border-l-2 border-orange-500"
          >
            <img 
              src={streak.image} 
              alt={streak.name}
              className="w-8 h-8 rounded-full object-cover"
              onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${streak.name}&size=32&background=FF6600&color=fff`; }}
            />
            <div className="flex-1 min-w-0">
              <span className="text-sm truncate block font-bold">{streak.name}</span>
              <span className="text-xs text-orange-400">{streak.streak_status}</span>
            </div>
            <div className="text-right">
              <div className="text-sm font-bold text-orange-400">
                {streak.streak_days} days
              </div>
              <div className="text-xs text-[#666]">
                {streak.tip}
              </div>
            </div>
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
        {watchList.slice(0, 6).map((celeb, idx) => (
          <div 
            key={celeb.id} 
            className={`flex items-center gap-3 p-2 hover:bg-[#1A1A1A] cursor-pointer ${celeb.is_premium ? 'border-l-2 border-[#FFD700] bg-[#FFD700]/5' : ''}`}
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
            <div className="text-right">
              <span className={`text-sm font-bold ${celeb.is_premium ? 'text-[#FFD700]' : 'text-[#A1A1AA]'}`}>
                £{celeb.price}M
              </span>
              {celeb.is_premium && <span className="block text-[8px] text-[#FFD700]">PREMIUM</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// League Panel Component
const LeaguePanel = ({ team, leagues, onCreateLeague, onJoinLeague, onViewLeague }) => {
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [newLeagueName, setNewLeagueName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  
  const handleCreate = () => {
    if (newLeagueName.trim()) {
      onCreateLeague(newLeagueName.trim());
      setNewLeagueName("");
      setShowCreate(false);
    }
  };
  
  const handleJoin = () => {
    if (joinCode.trim()) {
      onJoinLeague(joinCode.trim().toUpperCase());
      setJoinCode("");
      setShowJoin(false);
    }
  };
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="league-panel">
      <h4 className="font-anton text-lg uppercase tracking-tight text-[#00F0FF] mb-3 flex items-center gap-2">
        <Trophy className="w-5 h-5" />
        Friends Leagues
      </h4>
      
      {/* League Actions */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => { setShowCreate(true); setShowJoin(false); }}
          className="flex-1 bg-[#FF0099] text-white py-2 px-3 text-xs font-bold uppercase hover:bg-[#e6008a] transition-colors"
          data-testid="create-league-btn"
        >
          Create
        </button>
        <button
          onClick={() => { setShowJoin(true); setShowCreate(false); }}
          className="flex-1 bg-[#1A1A1A] border border-[#262626] text-white py-2 px-3 text-xs font-bold uppercase hover:border-[#00F0FF] transition-colors"
          data-testid="join-league-btn"
        >
          Join
        </button>
      </div>
      
      {/* Create League Form */}
      {showCreate && (
        <div className="bg-[#1A1A1A] p-3 mb-4">
          <input
            type="text"
            value={newLeagueName}
            onChange={(e) => setNewLeagueName(e.target.value)}
            placeholder="League name..."
            className="w-full bg-[#0A0A0A] border border-[#262626] p-2 text-sm mb-2 text-white"
            data-testid="league-name-input"
          />
          <button
            onClick={handleCreate}
            className="w-full bg-[#FFD700] text-black py-2 text-xs font-bold uppercase"
            data-testid="confirm-create-league"
          >
            Create League
          </button>
        </div>
      )}
      
      {/* Join League Form */}
      {showJoin && (
        <div className="bg-[#1A1A1A] p-3 mb-4">
          <input
            type="text"
            value={joinCode}
            onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
            placeholder="Enter code..."
            className="w-full bg-[#0A0A0A] border border-[#262626] p-2 text-sm mb-2 text-white uppercase tracking-widest text-center font-mono"
            maxLength={6}
            data-testid="join-code-input"
          />
          <button
            onClick={handleJoin}
            className="w-full bg-[#00F0FF] text-black py-2 text-xs font-bold uppercase"
            data-testid="confirm-join-league"
          >
            Join League
          </button>
        </div>
      )}
      
      {/* My Leagues List */}
      {leagues.length > 0 ? (
        <div className="space-y-2">
          {leagues.map((league) => (
            <div
              key={league.id}
              onClick={() => onViewLeague(league)}
              className="league-card cursor-pointer"
              data-testid={`league-${league.id}`}
            >
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-bold text-sm">{league.name}</p>
                  <p className="text-xs text-[#A1A1AA]">{league.team_ids?.length || 0} teams</p>
                </div>
                <div className="league-code text-sm">{league.code}</div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-xs text-[#666] text-center py-4">
          Create a league or join one with a code!
        </p>
      )}
    </div>
  );
};

// League Detail Modal
const LeagueDetailModal = ({ league, leaderboard, onClose, onShare, teamId }) => {
  const [copied, setCopied] = useState(false);
  const shareUrl = `${window.location.origin}?joinLeague=${league.code}`;
  const shareText = `Join my Celebrity Buzz league "${league.name}"! Use code: ${league.code} 🌟`;
  
  const handleCopyCode = async () => {
    try {
      await navigator.clipboard.writeText(league.code);
      setCopied(true);
      toast.success("Code copied!");
      setTimeout(() => setCopied(false), 2000);
    } catch (e) {
      toast.error("Failed to copy");
    }
  };
  
  const handleWhatsAppShare = () => {
    window.open(`https://wa.me/?text=${encodeURIComponent(shareText)}`, '_blank');
  };
  
  const handleXShare = () => {
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`, '_blank');
  };
  
  const handleFacebookShare = () => {
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(shareText)}`, '_blank');
  };
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#0A0A0A] border border-[#262626] max-w-lg w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-anton text-2xl uppercase text-[#FFD700]">{league.name}</h3>
            <button onClick={onClose} className="text-[#A1A1AA] hover:text-white">
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* League Code */}
          <div className="bg-[#1A1A1A] p-4 mb-4 text-center">
            <p className="text-xs text-[#A1A1AA] mb-2">INVITE CODE</p>
            <div className="league-code text-2xl mb-3">{league.code}</div>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={handleCopyCode}
                className="flex-1 min-w-[80px] bg-[#262626] text-white py-2 text-xs font-bold uppercase flex items-center justify-center gap-2"
              >
                {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                {copied ? "Copied!" : "Copy"}
              </button>
              <button
                onClick={handleWhatsAppShare}
                className="flex-1 min-w-[80px] bg-[#25D366] text-white py-2 text-xs font-bold uppercase"
                data-testid="league-share-whatsapp"
              >
                WhatsApp
              </button>
              <button
                onClick={handleXShare}
                className="flex-1 min-w-[80px] bg-black border border-white text-white py-2 text-xs font-bold uppercase"
                data-testid="league-share-x"
              >
                𝕏
              </button>
              <button
                onClick={handleFacebookShare}
                className="flex-1 min-w-[80px] bg-[#1877F2] text-white py-2 text-xs font-bold uppercase flex items-center justify-center gap-1"
                data-testid="league-share-facebook"
              >
                <Facebook className="w-3 h-3" />
                FB
              </button>
            </div>
          </div>
          
          {/* League Leaderboard */}
          <h4 className="font-anton text-lg uppercase text-[#00F0FF] mb-3">League Standings</h4>
          {leaderboard.length > 0 ? (
            <div className="space-y-2">
              {leaderboard.map((entry, idx) => (
                <div
                  key={entry.team_id}
                  className={`flex items-center gap-3 p-3 ${entry.team_id === teamId ? 'bg-[#FF0099]/20 border border-[#FF0099]' : 'bg-[#1A1A1A]'}`}
                >
                  <span className={`font-anton text-xl w-8 ${idx === 0 ? 'text-[#FFD700]' : idx === 1 ? 'text-[#C0C0C0]' : idx === 2 ? 'text-[#CD7F32]' : 'text-[#666]'}`}>
                    #{idx + 1}
                  </span>
                  <div className="flex-1">
                    <p className="font-bold text-sm flex items-center gap-2">
                      {entry.team_name}
                      {entry.is_owner && <Crown className="w-3 h-3 text-[#FFD700]" />}
                    </p>
                    <p className="text-xs text-[#A1A1AA]">{entry.celebrity_count} celebs</p>
                  </div>
                  <span className="font-space font-bold text-[#FF0099]">{entry.total_points?.toFixed(1)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-[#666] py-4">No teams yet!</p>
          )}
        </div>
      </div>
    </div>
  );
};

// Mobile Navigation Component
const MobileNav = ({ activeTab, onTabChange }) => (
  <div className="mobile-nav" data-testid="mobile-nav">
    <div className={`mobile-nav-item ${activeTab === 'home' ? 'active' : ''}`} onClick={() => onTabChange('home')}>
      <Home className="w-5 h-5" />
      <span>Home</span>
    </div>
    <div className={`mobile-nav-item ${activeTab === 'team' ? 'active' : ''}`} onClick={() => onTabChange('team')}>
      <Users className="w-5 h-5" />
      <span>Team</span>
    </div>
    <div className={`mobile-nav-item ${activeTab === 'leagues' ? 'active' : ''}`} onClick={() => onTabChange('leagues')}>
      <Trophy className="w-5 h-5" />
      <span>Leagues</span>
    </div>
  </div>
);

// Hall of Fame Modal
const HallOfFameModal = ({ hallOfFame, onClose }) => (
  <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
    <div className="bg-[#0A0A0A] border border-[#262626] max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="font-anton text-3xl uppercase text-[#FFD700] flex items-center gap-3">
            <span>🏆</span> Hall of Fame
          </h3>
          <button onClick={onClose} className="text-[#A1A1AA] hover:text-white">
            <X className="w-6 h-6" />
          </button>
        </div>
        
        {hallOfFame.length > 0 ? (
          <div className="space-y-4">
            {hallOfFame.map((entry, idx) => (
              <div 
                key={entry.team_id}
                className={`p-4 ${idx === 0 ? 'bg-gradient-to-r from-[#FFD700]/20 to-transparent border border-[#FFD700]' : idx === 1 ? 'bg-[#C0C0C0]/10 border border-[#C0C0C0]/30' : idx === 2 ? 'bg-[#CD7F32]/10 border border-[#CD7F32]/30' : 'bg-[#1A1A1A]'}`}
              >
                <div className="flex items-center gap-4">
                  <span className={`font-anton text-3xl w-12 ${idx === 0 ? 'text-[#FFD700]' : idx === 1 ? 'text-[#C0C0C0]' : idx === 2 ? 'text-[#CD7F32]' : 'text-[#666]'}`}>
                    #{idx + 1}
                  </span>
                  <div className="flex-1">
                    <p className="font-bold text-lg">{entry.team_name}</p>
                    <div className="flex gap-1 mt-1">
                      {entry.badges.map((badge, bIdx) => (
                        <span key={bIdx} className="text-xl" title={badge.name}>
                          {badge.icon}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-[#FF0099]">{entry.badge_count} badges</p>
                    <p className="text-xs text-[#A1A1AA]">{entry.weekly_wins} weekly wins</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-2xl mb-2">🏆</p>
            <p className="text-[#A1A1AA]">No champions yet!</p>
            <p className="text-xs text-[#666] mt-2">Win weekly league competitions to earn badges and join the Hall of Fame</p>
          </div>
        )}
      </div>
    </div>
  </div>
);

// Team Customization Modal
const TeamCustomizeModal = ({ team, options, onSave, onClose }) => {
  const [teamName, setTeamName] = useState(team?.team_name || "");
  const [selectedColor, setSelectedColor] = useState(team?.team_color || "pink");
  const [selectedIcon, setSelectedIcon] = useState(team?.team_icon || "star");
  
  const handleSave = () => {
    onSave(teamName, selectedColor, selectedIcon);
  };
  
  const selectedColorHex = options.colors?.find(c => c.id === selectedColor)?.hex || "#FF0099";
  const selectedIconEmoji = options.icons?.find(i => i.id === selectedIcon)?.emoji || "⭐";
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#0A0A0A] border border-[#262626] max-w-md w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-anton text-2xl uppercase text-[#00F0FF]">Customize Team</h3>
            <button onClick={onClose} className="text-[#A1A1AA] hover:text-white">
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Preview */}
          <div className="bg-[#1A1A1A] p-4 mb-6 text-center">
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3 text-3xl"
              style={{ backgroundColor: selectedColorHex }}
            >
              {selectedIconEmoji}
            </div>
            <p className="font-bold text-lg">{teamName || "My Team"}</p>
            <p className="text-xs text-[#A1A1AA]">Preview</p>
          </div>
          
          {/* Team Name */}
          <div className="mb-6">
            <label className="block text-sm text-[#A1A1AA] mb-2">Team Name</label>
            <input
              type="text"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              className="w-full bg-[#1A1A1A] border border-[#262626] p-3 text-white"
              placeholder="Enter team name..."
              maxLength={30}
            />
          </div>
          
          {/* Colors */}
          <div className="mb-6">
            <label className="block text-sm text-[#A1A1AA] mb-2">Team Color</label>
            <div className="grid grid-cols-4 gap-2">
              {options.colors?.map((color) => (
                <button
                  key={color.id}
                  onClick={() => setSelectedColor(color.id)}
                  className={`w-full aspect-square rounded-lg border-2 transition-all ${selectedColor === color.id ? 'border-white scale-110' : 'border-transparent'}`}
                  style={{ backgroundColor: color.hex }}
                  title={color.name}
                />
              ))}
            </div>
          </div>
          
          {/* Icons */}
          <div className="mb-6">
            <label className="block text-sm text-[#A1A1AA] mb-2">Team Icon</label>
            <div className="grid grid-cols-6 gap-2">
              {options.icons?.map((icon) => (
                <button
                  key={icon.id}
                  onClick={() => setSelectedIcon(icon.id)}
                  className={`text-2xl p-2 rounded-lg border-2 transition-all ${selectedIcon === icon.id ? 'border-[#00F0FF] bg-[#1A1A1A]' : 'border-transparent hover:bg-[#1A1A1A]'}`}
                  title={icon.name}
                >
                  {icon.emoji}
                </button>
              ))}
            </div>
          </div>
          
          {/* Save Button */}
          <button
            onClick={handleSave}
            className="w-full bg-gradient-to-r from-[#FF0099] to-[#00F0FF] text-white font-bold py-3 uppercase"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

// How It Works Component
const HowItWorks = ({ onShowMethodology }) => (
  <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-8" data-testid="how-it-works">
    <div className="flex justify-between items-center mb-3">
      <h3 className="font-anton text-lg uppercase tracking-tight text-[#FFD700]">How It Works</h3>
      <button 
        onClick={onShowMethodology}
        className="flex items-center gap-1 text-[#00F0FF] hover:text-white text-xs"
        data-testid="show-methodology-btn"
      >
        <Info className="w-3 h-3" />
        Points Info
      </button>
    </div>
    <div className="grid grid-cols-5 gap-2">
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FF0099] flex items-center justify-center mx-auto mb-2">
          <Search className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm">Search</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Find any celeb</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#00F0FF] flex items-center justify-center mx-auto mb-2">
          <Star className="w-5 h-5 text-black" />
        </div>
        <h4 className="font-space font-bold text-sm">£0.5-12M</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Tier pricing</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FFD700] flex items-center justify-center mx-auto mb-2">
          <Plus className="w-5 h-5 text-black" />
        </div>
        <h4 className="font-space font-bold text-sm">£50M</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Your budget</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FF5500] flex items-center justify-center mx-auto mb-2">
          <ArrowLeftRight className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm">Sat 12pm</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Transfer window</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#8B5CF6] flex items-center justify-center mx-auto mb-2">
          <Skull className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm">+100</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Brown Bread</p>
      </div>
    </div>
  </div>
);

// Header Component
const Header = () => (
  <header className="py-4 md:py-8 px-2 text-center">
    <h1 className="font-anton text-[2.5rem] sm:text-6xl md:text-7xl lg:text-8xl tracking-tighter uppercase header-title leading-none" data-testid="main-title">
      <span className="text-[#FFD700]">C</span>
      <span className="text-[#FF0099]">e</span>
      <span>l</span>
      <span className="text-[#FF0099]">e</span>
      <span>b</span>
      <span className="text-[#00F0FF]">r</span>
      <span>i</span>
      <span className="text-[#FF0099]">t</span>
      <span>y</span>
    </h1>
    <h1 className="font-anton text-[2.5rem] sm:text-6xl md:text-7xl lg:text-8xl tracking-tighter uppercase header-title leading-none" data-testid="main-title-2">
      <span className="text-[#FFD700]">B</span>
      <span className="text-[#FF0099]">u</span>
      <span>z</span>
      <span className="text-[#00F0FF]">z</span>
      <span className="mx-2 sm:mx-3 md:mx-4"></span>
      <span className="text-[#FFD700]">I</span>
      <span className="text-[#FF0099]">n</span>
      <span>d</span>
      <span className="text-[#00F0FF]">e</span>
      <span>x</span>
    </h1>
    <p className="font-space text-[#A1A1AA] mt-2 md:mt-4 text-xs sm:text-sm uppercase tracking-[2px] sm:tracking-[4px]">
      Build Your Dream Celebrity Team
    </p>
  </header>
);

// Hot Celebs Scrolling Ticker Component (replaces old TrendingTicker)
const HotCelebsTicker = ({ celebs, onSelect }) => {
  if (!celebs || celebs.length === 0) return null;
  
  // Double the list for infinite scroll effect
  const doubled = [...celebs, ...celebs];
  
  return (
    <div className="hot-celebs-ticker-container" data-testid="hot-celebs-ticker">
      <div className="hot-celebs-ticker-content">
        {doubled.map((celeb, idx) => (
          <span 
            key={idx} 
            className="ticker-item flex items-center gap-3 cursor-pointer hover:opacity-80 transition-opacity"
            onClick={() => onSelect && onSelect(celeb.name)}
          >
            <img 
              src={celeb.image || `https://ui-avatars.com/api/?name=${celeb.name}&size=40&background=FF0099&color=fff`}
              alt={celeb.name}
              className="w-10 h-10 rounded-full object-cover border-2 border-black shadow-lg"
              onError={(e) => {
                e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=40&background=FF0099&color=fff`;
              }}
            />
            <span className="font-bold text-white">{celeb.name}</span>
            {celeb.tier && <TierBadge tier={celeb.tier} />}
            <span className="bg-black/80 px-2 py-0.5 text-[#00FF00] font-bold text-sm">£{celeb.price}M</span>
            <span className="text-[10px] text-[#FF0099]">🔥 {celeb.hot_reason}</span>
          </span>
        ))}
      </div>
    </div>
  );
};

// Category Filter Component
const CategoryFilter = ({ categories, activeCategory, onSelect }) => (
  <div className="flex flex-wrap gap-3 justify-center py-6 px-4 mb-6" data-testid="category-filter">
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
    <div ref={searchRef} className="search-container mb-2 px-4 relative">
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
      
      {/* Helper text - directly under search bar */}
      <p className="text-center text-base text-[#FFD700] mt-3 mb-2 font-medium" data-testid="search-helper-text">
        Select a category or search for any celebrity
      </p>
      
      {/* Autocomplete Suggestions */}
      {showSuggestions && (suggestions.length > 0 || loadingSuggestions) && (
        <div className="absolute left-4 right-4 top-[55px] bg-[#0A0A0A] border border-[#262626] max-h-96 overflow-y-auto z-50" data-testid="autocomplete-dropdown">
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
const CelebrityCard = ({ celebrity, onAdd, isInTeam, canAfford, onShowPriceHistory }) => {
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
        <div className="buzz-score hidden" data-testid={`buzz-score-${celebrity.id}`}>
          {celebrity.buzz_score?.toFixed(1)}
        </div>
        {/* Tier badge top left */}
        <div className="absolute top-3 left-3">
          <TierBadge tier={celebrity.tier || "D"} />
        </div>
        {/* Price history button top right */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onShowPriceHistory(celebrity.name);
          }}
          className="absolute top-3 right-3 bg-[#0A0A0A]/80 p-1.5 hover:bg-[#FF0099] transition-colors"
          title="View price history"
          data-testid={`price-history-btn-${celebrity.id}`}
        >
          <LineChart className="w-4 h-4 text-[#00F0FF]" />
        </button>
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
const TeamPanel = ({ team, onRemove, onShare, onCustomize }) => {
  if (!team) return null;
  
  // Get team color and icon
  const teamColorHex = team.team_color === 'pink' ? '#FF0099' : 
                       team.team_color === 'cyan' ? '#00F0FF' :
                       team.team_color === 'gold' ? '#FFD700' :
                       team.team_color === 'purple' ? '#8B5CF6' :
                       team.team_color === 'red' ? '#EF4444' :
                       team.team_color === 'green' ? '#10B981' :
                       team.team_color === 'orange' ? '#F97316' :
                       team.team_color === 'white' ? '#FFFFFF' : '#FF0099';
                       
  const teamIconEmoji = team.team_icon === 'star' ? '⭐' :
                        team.team_icon === 'crown' ? '👑' :
                        team.team_icon === 'fire' ? '🔥' :
                        team.team_icon === 'lightning' ? '⚡' :
                        team.team_icon === 'rocket' ? '🚀' :
                        team.team_icon === 'diamond' ? '💎' :
                        team.team_icon === 'skull' ? '💀' :
                        team.team_icon === 'ghost' ? '👻' :
                        team.team_icon === 'alien' ? '👽' :
                        team.team_icon === 'robot' ? '🤖' :
                        team.team_icon === 'unicorn' ? '🦄' :
                        team.team_icon === 'dragon' ? '🐉' : '⭐';
  
  return (
    <div className="team-panel" data-testid="team-panel">
      <div className="team-header">
        <div className="flex items-center gap-3">
          {/* Team Icon */}
          <div 
            className="w-12 h-12 rounded-full flex items-center justify-center text-xl cursor-pointer hover:scale-110 transition-transform"
            style={{ backgroundColor: teamColorHex }}
            onClick={onCustomize}
            title="Customize Team"
          >
            {teamIconEmoji}
          </div>
          <div>
            <h3 className="font-anton text-2xl uppercase tracking-tight">{team.team_name}</h3>
            <p className="text-sm text-[#A1A1AA] font-space">
              {team.celebrities?.length || 0} celebrities • {team.total_points?.toFixed(1)} points
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="budget-display" data-testid="budget-display">
            £{team.budget_remaining}M
          </div>
          <p className="text-xs text-[#A1A1AA] uppercase tracking-wider">Budget Left</p>
          <p className="text-xs text-[#666] mt-1">{team.celebrities?.length || 0}/10 players</p>
        </div>
      </div>
      
      {/* Badges Display */}
      {team.badges?.length > 0 && (
        <div className="flex gap-1 mt-3 flex-wrap">
          {team.badges.map((badge, idx) => (
            <span 
              key={idx} 
              className="text-lg cursor-help" 
              title={`${badge.name || badge.id}: ${badge.description || ''}`}
            >
              {badge.icon || '🏅'}
            </span>
          ))}
        </div>
      )}
      
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
                  <span className="text-[#FFD700]">£{celeb.price}M</span>
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
          {/* Team Icon */}
          <div 
            className="w-8 h-8 rounded-full flex items-center justify-center text-sm ml-2"
            style={{ backgroundColor: entry.team_color || '#FF0099' }}
          >
            {entry.team_icon || '⭐'}
          </div>
          <div className="flex-1 ml-3">
            <p className="font-bold flex items-center gap-1">
              {entry.team_name}
              {/* Show first 3 badges */}
              {entry.badges?.slice(0, 3).map((b, i) => (
                <span key={i} className="text-sm">{b.icon || '🏅'}</span>
              ))}
            </p>
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
  const [brownBreadWatch, setBrownBreadWatch] = useState([]);
  const [hotCelebs, setHotCelebs] = useState([]);
  const [priceAlerts, setPriceAlerts] = useState([]);
  const [hotStreaks, setHotStreaks] = useState([]);
  
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
  
  // Mobile tab state
  const [mobileTab, setMobileTab] = useState('home');
  
  // Handler to show price history
  const handleShowPriceHistory = (celebrityName) => {
    setPriceHistoryCeleb(celebrityName);
    setShowPriceHistory(true);
  };

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

  // Fetch hot celebs this week
  const fetchHotCelebs = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/hot-celebs`);
      setHotCelebs(res.data.hot_celebs || []);
    } catch (e) {
      console.error("Error fetching hot celebs:", e);
    }
  }, []);

  // Fetch Brown Bread Watch (elderly celebs)
  const fetchBrownBreadWatch = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/brown-bread-watch`);
      setBrownBreadWatch(res.data.watch_list || []);
    } catch (e) {
      console.error("Error fetching brown bread watch:", e);
    }
  }, []);

  // Fetch price alerts for team
  const fetchPriceAlerts = useCallback(async (teamId) => {
    if (!teamId) return;
    try {
      const res = await axios.get(`${API}/price-alerts/${teamId}`);
      setPriceAlerts(res.data.alerts || []);
    } catch (e) {
      console.error("Error fetching price alerts:", e);
    }
  }, []);

  // Fetch hot streaks for team
  const fetchHotStreaks = useCallback(async (teamId) => {
    if (!teamId) return;
    try {
      const res = await axios.get(`${API}/hot-streaks/${teamId}`);
      setHotStreaks(res.data.hot_streaks || []);
    } catch (e) {
      console.error("Error fetching hot streaks:", e);
    }
  }, []);

  // Fetch team's leagues
  const fetchTeamLeagues = useCallback(async (teamId) => {
    try {
      const res = await axios.get(`${API}/team/${teamId}/leagues`);
      setLeagues(res.data.leagues || []);
    } catch (e) {
      console.error("Error fetching leagues:", e);
    }
  }, []);

  // Fetch Hall of Fame
  const fetchHallOfFame = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/hall-of-fame`);
      setHallOfFame(res.data.hall_of_fame || []);
    } catch (e) {
      console.error("Error fetching hall of fame:", e);
    }
  }, []);

  // Fetch customization options
  const fetchCustomOptions = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/team/customization-options`);
      setCustomOptions(res.data);
    } catch (e) {
      console.error("Error fetching customization options:", e);
    }
  }, []);

  // Customize team
  const customizeTeam = async (teamName, teamColor, teamIcon) => {
    if (!team) return;
    try {
      const res = await axios.post(`${API}/team/customize`, {
        team_id: team.id,
        team_name: teamName || undefined,
        team_color: teamColor || undefined,
        team_icon: teamIcon || undefined
      });
      setTeam(res.data.team);
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
      const res = await axios.post(`${API}/league/create`, {
        name,
        team_id: team.id
      });
      setLeagues(prev => [...prev, res.data.league]);
      toast.success(`League "${name}" created! Share code: ${res.data.league.code}`);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create league");
    }
  };

  // Join a league
  const joinLeague = async (code) => {
    if (!team) return;
    try {
      const res = await axios.post(`${API}/league/join`, {
        code,
        team_id: team.id
      });
      setLeagues(prev => [...prev, res.data.league]);
      toast.success(res.data.message);
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to join league");
    }
  };

  // View league details
  const viewLeague = async (league) => {
    try {
      const res = await axios.get(`${API}/league/${league.id}/leaderboard`);
      setLeagueLeaderboard(res.data.leaderboard || []);
      setSelectedLeague(league);
    } catch (e) {
      toast.error("Failed to load league");
    }
  };

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

  // Handle clicking on a celeb in the hot celebs ticker
  const handleCelebSearch = (name) => {
    searchCelebrity(name);
  };

  // Create or get team
  const initTeam = useCallback(async () => {
    // Check localStorage for existing team
    const storedTeamId = localStorage.getItem("teamId");
    if (storedTeamId) {
      try {
        const res = await axios.get(`${API}/team/${storedTeamId}`);
        setTeam(res.data.team);
        // Fetch team's leagues
        fetchTeamLeagues(storedTeamId);
        // Fetch price alerts
        fetchPriceAlerts(storedTeamId);
        // Fetch hot streaks
        fetchHotStreaks(storedTeamId);
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
  }, [fetchTeamLeagues, fetchPriceAlerts, fetchHotStreaks]);

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
    fetchBrownBreadWatch();
    fetchHotCelebs();
  }, [fetchCategories, fetchTrending, initTeam, fetchLeaderboard, fetchStats, fetchTodaysNews, fetchTopPicked, fetchBrownBreadWatch, fetchHotCelebs]);

  return (
    <div className="App">
      <Toaster position="top-right" theme="dark" richColors />
      <div className="noise-overlay"></div>
      
      <TransferWindowBanner stats={stats} />
      <Header />
      
      <div className="max-w-7xl mx-auto px-4">
        <HowItWorks onShowMethodology={() => setShowMethodology(true)} />
      </div>
      
      <HotCelebsBanner celebs={hotCelebs} onSelect={handleCelebSearch} />
      
      <div className="max-w-7xl mx-auto px-4 py-8">
        <SearchBar onSearch={searchCelebrity} loading={searchLoading} />
        <CategoryFilter 
          categories={categories} 
          activeCategory={activeCategory} 
          onSelect={handleCategoryChange} 
        />
        
        {/* Celebrity Grid - Now above news so searched celebs show immediately */}
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
        
        {/* Team Panel - Right after search results */}
        <div className="mb-6">
          <TeamPanel 
            team={team} 
            onRemove={removeFromTeam}
            onShare={() => setShowShareModal(true)}
            onCustomize={() => { fetchCustomOptions(); setShowCustomize(true); }}
          />
        </div>
        
        <TodaysNews news={todaysNews} />
        
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
            <HotStreaks streaks={hotStreaks} teamId={team?.id} />
            <TopPickedCelebs celebs={topPicked} onSelect={searchCelebrity} />
            <BrownBreadWatch watchList={brownBreadWatch} onSelect={searchCelebrity} />
            <Leaderboard entries={leaderboard} />
            
            {/* Hall of Fame Button */}
            <button
              onClick={() => { fetchHallOfFame(); setShowHallOfFame(true); }}
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
      
      {/* Mobile Navigation */}
      <MobileNav activeTab={mobileTab} onTabChange={setMobileTab} />
      
      {/* Footer */}
      <Footer />
    </div>
  );
}

export default App;
