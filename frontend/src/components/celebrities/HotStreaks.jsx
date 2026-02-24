import { useState, useEffect } from "react";
import { Flame, TrendingUp } from "lucide-react";
import TierBadge from "../common/TierBadge";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const HotStreaks = ({ streaks: propStreaks, onCelebClick }) => {
  const [streaks, setStreaks] = useState(propStreaks || []);
  const [loading, setLoading] = useState(!propStreaks);
  const [showAlert, setShowAlert] = useState(false);
  const [alertCeleb, setAlertCeleb] = useState(null);

  useEffect(() => {
    // If streaks passed as props, use those
    if (propStreaks && propStreaks.length > 0) {
      setStreaks(propStreaks);
      setLoading(false);
      checkForAlerts(propStreaks);
    } else {
      fetchHotStreaks();
    }
  }, [propStreaks]);

  const checkForAlerts = (streakData) => {
    // Show alert for the top streak celebrity (if any with 5+ days)
    const topStreak = streakData?.find(s => s.streak_days >= 5);
    if (topStreak && !sessionStorage.getItem(`streak_alert_${topStreak.name}`)) {
      setAlertCeleb(topStreak);
      setShowAlert(true);
      sessionStorage.setItem(`streak_alert_${topStreak.name}`, 'shown');
    }
  };

  const fetchHotStreaks = async () => {
    try {
      const response = await fetch(`${API_URL}/api/hot-streaks`);
      if (response.ok) {
        const data = await response.json();
        setStreaks(data.hot_streaks || []);
        checkForAlerts(data.hot_streaks);
      }
    } catch (error) {
      console.error("Error fetching hot streaks:", error);
    } finally {
      setLoading(false);
    }
  };

  const dismissAlert = () => {
    setShowAlert(false);
    setAlertCeleb(null);
  };

  const getStreakIcon = (days) => {
    if (days >= 6) return "🔥🔥🔥";
    if (days >= 5) return "🔥🔥";
    if (days >= 4) return "🔥";
    return "⚡";
  };

  const getStreakColor = (days) => {
    if (days >= 6) return "text-red-500";
    if (days >= 5) return "text-orange-500";
    if (days >= 4) return "text-yellow-500";
    return "text-cyan-400";
  };

  if (loading) {
    return (
      <div className="bg-[#0D0D0D] border border-[#1A1A1A] rounded-lg p-4">
        <div className="flex items-center gap-2 mb-3">
          <Flame className="w-5 h-5 text-orange-500" />
          <h3 className="text-white font-bold">Hot Streaks</h3>
        </div>
        <div className="text-center text-[#A1A1AA] py-4">Loading...</div>
      </div>
    );
  }

  if (streaks.length === 0) {
    return null; // Don't show component if no streaks
  }

  return (
    <>
      {/* In-App Alert */}
      {showAlert && alertCeleb && (
        <div 
          className="fixed top-4 right-4 z-50 max-w-sm bg-gradient-to-r from-orange-600 to-red-600 rounded-lg shadow-lg p-4 animate-pulse"
          data-testid="hot-streak-alert"
        >
          <div className="flex items-start gap-3">
            <div className="text-2xl">{getStreakIcon(alertCeleb.streak_days)}</div>
            <div className="flex-1">
              <h4 className="text-white font-bold text-sm">HOT STREAK ALERT!</h4>
              <p className="text-white/90 text-sm mt-1">
                <span className="font-bold">{alertCeleb.name}</span> has been trending for {alertCeleb.streak_days} days straight!
              </p>
              <p className="text-white/70 text-xs mt-1">
                {alertCeleb.news_count} news articles this week
              </p>
            </div>
            <button 
              onClick={dismissAlert}
              className="text-white/70 hover:text-white text-lg"
              data-testid="dismiss-alert"
            >
              ×
            </button>
          </div>
          <button
            onClick={() => {
              onCelebClick?.(alertCeleb.name);
              dismissAlert();
            }}
            className="mt-3 w-full bg-white/20 hover:bg-white/30 text-white text-sm py-2 rounded transition-colors"
            data-testid="view-celeb-btn"
          >
            View Celebrity →
          </button>
        </div>
      )}

      {/* Hot Streaks List */}
      <div className="bg-[#0D0D0D] border border-[#1A1A1A] rounded-lg p-4" data-testid="hot-streaks-container">
        <div className="flex items-center gap-2 mb-3">
          <Flame className="w-5 h-5 text-orange-500" />
          <h3 className="text-white font-bold text-sm">Hot Streaks</h3>
          <span className="text-xs text-[#A1A1AA]">(3+ days trending)</span>
        </div>
        
        <div className="space-y-2 max-h-[280px] overflow-y-auto">
          {streaks.map((streak, idx) => (
            <div
              key={idx}
              onClick={() => onCelebClick?.(streak.name)}
              className="flex items-center gap-2 p-2 bg-[#1A1A1A] rounded hover:bg-[#252525] cursor-pointer transition-colors"
              data-testid={`streak-item-${idx}`}
            >
              {/* Streak indicator */}
              <div className={`text-sm ${getStreakColor(streak.streak_days)}`}>
                {getStreakIcon(streak.streak_days)}
              </div>
              
              {/* Celebrity image */}
              <img
                src={streak.image || `https://ui-avatars.com/api/?name=${streak.name}&size=32&background=FF0099&color=fff`}
                alt={streak.name}
                className="w-8 h-8 rounded-full object-cover"
                onError={(e) => {
                  e.target.src = `https://ui-avatars.com/api/?name=${streak.name}&size=32&background=FF0099&color=fff`;
                }}
              />
              
              {/* Name and tier */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="text-white text-sm font-medium truncate">{streak.name}</span>
                  <TierBadge tier={streak.tier} size="xs" />
                </div>
                <div className="text-xs text-[#A1A1AA]">
                  {streak.streak_days} days · {streak.news_count} articles
                </div>
              </div>
              
              {/* Price */}
              <div className="text-right">
                <div className="text-[#FFD700] text-sm font-bold">£{streak.price}M</div>
                <div className="flex items-center gap-0.5 text-green-400 text-xs">
                  <TrendingUp className="w-3 h-3" />
                  <span>Hot</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        <p className="text-xs text-[#666] mt-3 text-center">
          Celebrities in the news for 3+ consecutive days
        </p>
      </div>
    </>
  );
};

export default HotStreaks;
