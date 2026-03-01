import { useState, useEffect } from "react";
import { X, Copy, Check, Facebook, TrendingUp, TrendingDown, LineChart, Skull } from "lucide-react";
import { toast } from "sonner";
import { fetchPriceHistory } from "../../api";

// Share Modal Component with WhatsApp, X, Facebook
export const ShareModal = ({ team, onClose }) => {
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

// Points Methodology Component
export const PointsMethodology = ({ onClose }) => (
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
            <span className="text-sm">£10m-£15m • High scoring but expensive</span>
          </div>
          <div className="bg-[#C0C0C0] text-black p-2 flex justify-between items-center">
            <span className="font-bold">B-LIST</span>
            <span className="text-sm">£4m-£6.9m • Balanced steady picks</span>
          </div>
          <div className="bg-[#CD7F32] text-white p-2 flex justify-between items-center">
            <span className="font-bold">C-LIST</span>
            <span className="text-sm">£1.5m-£2.9m • Risk/reward</span>
          </div>
          <div className="bg-[#666666] text-white p-2 flex justify-between items-center">
            <span className="font-bold">D-LIST</span>
            <span className="text-sm">£0.5m-£1m • Cheap wildcards</span>
          </div>
        </div>
        
        <div className="bg-[#00F0FF]/10 border border-[#00F0FF] p-4 mb-4">
          <h4 className="font-bold text-[#00F0FF] mb-2">📈 Dynamic Pricing</h4>
          <p className="text-sm text-[#A1A1AA]">Prices fluctuate weekly based on media coverage. Hot celebs cost more, quiet celebs cost less!</p>
        </div>
        
        <div className="bg-[#FF0099]/20 border border-[#FF0099] p-4 mb-4">
          <h4 className="font-bold text-[#FF0099] mb-2">🕐 Transfer Window</h4>
          <p className="text-sm text-[#A1A1AA]">Opens every <span className="text-white font-bold">Sunday 12pm - 12am GMT</span>. Make your moves!</p>
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

// Price History Modal Component
export const PriceHistoryModal = ({ celebrityName, onClose }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPrice, setCurrentPrice] = useState(0);
  const [currentTier, setCurrentTier] = useState("D");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const data = await fetchPriceHistory(celebrityName);
        setHistory(data.history || []);
        setCurrentPrice(data.current_price || 0);
        setCurrentTier(data.current_tier || "D");
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

// Hall of Fame Modal
export const HallOfFameModal = ({ hallOfFame, onClose }) => (
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

// Price Alerts Component - Shows upcoming price changes for team
export const PriceAlerts = ({ alerts, teamId }) => {
  const { Bell } = require("lucide-react");
  
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
export const HotStreaks = ({ streaks, teamId }) => {
  const [dismissed, setDismissed] = useState([]);
  const [showNotification, setShowNotification] = useState(false);
  
  // Request notification permission and show browser notification for new streaks
  useEffect(() => {
    if (streaks && streaks.length > 0) {
      // Check if we have new hot streaks
      const newStreaks = streaks.filter(s => !dismissed.includes(s.celebrity_id));
      
      if (newStreaks.length > 0 && "Notification" in window) {
        // Request permission if not already granted
        if (Notification.permission === "granted") {
          // Show notification for the hottest streak
          const hottest = newStreaks[0];
          new Notification("🔥 Hot Streak Alert!", {
            body: `${hottest.name} is ${hottest.streak_status} - ${hottest.streak_days} days of headlines!`,
            icon: hottest.image || "/favicon.ico",
            tag: `hot-streak-${hottest.celebrity_id}`,
          });
          setShowNotification(true);
        } else if (Notification.permission !== "denied") {
          Notification.requestPermission();
        }
      }
    }
  }, [streaks, dismissed]);
  
  const dismissStreak = (celebId) => {
    setDismissed(prev => [...prev, celebId]);
  };
  
  const activeStreaks = streaks?.filter(s => !dismissed.includes(s.celebrity_id)) || [];
  
  if (activeStreaks.length === 0) {
    return null;
  }
  
  return (
    <div className="bg-gradient-to-r from-orange-500/20 via-[#0A0A0A] to-red-500/20 border border-orange-500/50 p-4 mb-4 rounded-lg animate-pulse-slow relative" data-testid="hot-streaks">
      {/* Notification badge */}
      {showNotification && (
        <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full animate-bounce">
          NEW!
        </div>
      )}
      
      <h4 className="font-anton text-xl uppercase tracking-tight text-orange-400 mb-3 flex items-center gap-2">
        <span className="animate-pulse">🔥</span> Hot Streak Alerts
        <span className="text-sm font-normal text-orange-300">({activeStreaks.length} active)</span>
      </h4>
      <p className="text-xs text-[#888] mb-3">Your team members making headlines 3+ days in a row! Price increases likely.</p>
      <div className="space-y-3">
        {activeStreaks.slice(0, 5).map((streak, idx) => (
          <div 
            key={idx}
            className="flex items-center gap-3 p-3 bg-gradient-to-r from-orange-500/10 to-red-500/10 border-l-4 border-orange-500 rounded-r-lg hover:from-orange-500/20 hover:to-red-500/20 transition-all group"
          >
            <div className="relative">
              <img 
                src={streak.image} 
                alt={streak.name}
                className="w-12 h-12 rounded-full object-cover border-2 border-orange-500"
                onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${streak.name}&size=48&background=FF6600&color=fff`; }}
              />
              <div className="absolute -bottom-1 -right-1 bg-orange-500 rounded-full w-5 h-5 flex items-center justify-center text-xs">
                {streak.streak_days}
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-sm truncate block font-bold text-white">{streak.name}</span>
              <span className="text-sm text-orange-400 font-semibold">{streak.streak_status}</span>
              <span className="text-xs text-[#888] block mt-1">{streak.tip}</span>
            </div>
            <div className="text-right flex flex-col items-end gap-1">
              <div className="text-lg font-bold text-orange-400 flex items-center gap-1">
                <span className="text-2xl">{streak.streak_days}</span>
                <span className="text-xs text-orange-300">DAYS</span>
              </div>
              <button 
                onClick={() => dismissStreak(streak.celebrity_id)}
                className="text-xs text-[#666] hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
              >
                Dismiss
              </button>
            </div>
          </div>
        ))}
      </div>
      
      {/* Enable notifications CTA */}
      {"Notification" in window && Notification.permission === "default" && (
        <button 
          onClick={() => Notification.requestPermission()}
          className="mt-3 text-xs text-orange-400 hover:text-orange-300 underline"
        >
          Enable browser notifications for hot streak alerts
        </button>
      )}
    </div>
  );
};
