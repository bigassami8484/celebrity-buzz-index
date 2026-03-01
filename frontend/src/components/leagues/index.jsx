import { useState, useEffect, useRef, useCallback } from "react";
import { Trophy, Crown, X, Copy, Check, Facebook, Calendar, CalendarDays, Users, Award, ChevronRight, ChevronDown, ChevronUp, Star, MessageCircle, Send } from "lucide-react";
import { toast } from "sonner";

// Badge icons mapping
const BADGE_ICONS = {
  weekly_winner: "🏆",
  monthly_winner: "🌟",
  league_champion: "👑",
  league_founder: "🎯",
  undefeated: "💪",
  brown_bread: "💀",
  controversy_king: "🔥",
  a_lister: "⭐",
  first_pick: "⚡",
};

// Team color mapping
const TEAM_COLORS = {
  pink: "#FF0099",
  cyan: "#00F0FF",
  gold: "#FFD700",
  green: "#10B981",
  purple: "#8B5CF6",
  orange: "#F97316",
  blue: "#3B82F6",
  red: "#EF4444",
};

// League Panel Component
export const LeaguePanel = ({ team, leagues, onCreateLeague, onJoinLeague, onViewLeague }) => {
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
          <p className="text-xs text-[#A1A1AA] mb-2">Max 10 friends per league</p>
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
            placeholder="Enter 6-digit code..."
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
              className="league-card cursor-pointer group"
              data-testid={`league-${league.id}`}
            >
              <div className="flex justify-between items-center">
                <div>
                  <p className="font-bold text-sm flex items-center gap-2">
                    {league.name}
                    {league.owner_team_id === team?.id && <Crown className="w-3 h-3 text-[#FFD700]" />}
                  </p>
                  <p className="text-xs text-[#A1A1AA]">
                    <Users className="w-3 h-3 inline mr-1" />
                    {league.team_ids?.length || 0}/10 friends
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="league-code text-sm">{league.code}</div>
                  <ChevronRight className="w-4 h-4 text-[#666] group-hover:text-[#00F0FF] transition-colors" />
                </div>
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

// League Detail Modal with Weekly/Monthly/Chat Tabs
export const LeagueDetailModal = ({ league, leaderboard, onClose, teamId, apiUrl }) => {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState("weekly");
  const [weeklyData, setWeeklyData] = useState(null);
  const [monthlyData, setMonthlyData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [newMessage, setNewMessage] = useState("");
  const [sendingMessage, setSendingMessage] = useState(false);
  const chatEndRef = useRef(null);

  // ✅ Wrap the functions in useCallback so they can be safely added to useEffect dependencies
  const fetchLeagueData = useCallback(async () => {
    setLoading(true);
    try {
      const [weeklyRes, monthlyRes, statsRes] = await Promise.all([
        fetch(`${apiUrl}/api/league/${league.id}/weekly-leaderboard`),
        fetch(`${apiUrl}/api/league/${league.id}/monthly-leaderboard`),
        fetch(`${apiUrl}/api/league/${league.id}/stats`)
      ]);
      
      if (weeklyRes.ok) setWeeklyData(await weeklyRes.json());
      if (monthlyRes.ok) setMonthlyData(await monthlyRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch (e) {
      console.error("Error fetching league data:", e);
    }
    setLoading(false);
  }, [league.id, apiUrl]);

  const fetchChatMessages = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/league/${league.id}/chat`);
      if (res.ok) {
        const data = await res.json();
        setChatMessages(data.messages || []);
      }
    } catch (e) {
      console.error("Error fetching chat:", e);
    }
  }, [league.id, apiUrl]);

  useEffect(() => {
    fetchLeagueData();
  }, [fetchLeagueData]); // ✅ Add as dependency

  useEffect(() => {
    if (activeTab === "chat") {
      fetchChatMessages();
      const interval = setInterval(fetchChatMessages, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab, fetchChatMessages]); // ✅ Add as dependency

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);

  const sendMessage = async () => {
    if (!newMessage.trim() || sendingMessage) return;
    
    setSendingMessage(true);
    try {
      const res = await fetch(`${apiUrl}/api/league/${league.id}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_id: teamId, message: newMessage.trim() })
      });
      
      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, data.chat_message]);
        setNewMessage("");
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to send message");
      }
    } catch (e) {
      toast.error("Failed to send message");
    }
    setSendingMessage(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // …rest of your component code stays the same
  // No other ESLint dependency issues remain
};

// Leaderboard & BadgesDisplay components stay the same
export const Leaderboard = ({ entries }) => {
  const [expanded, setExpanded] = useState(false);
  const displayCount = expanded ? 10 : 5;
  const placeholderRows = Array.from({ length: displayCount }, (_, i) => i + 1);
  
  return (
    <div className="leaderboard h-full" data-testid="leaderboard">
      <h3 className="font-anton text-2xl uppercase tracking-tight mb-2">Leaderboard</h3>
      <p className="text-xs text-[#A1A1AA] mb-4 flex items-center gap-1">
        <span className="text-[#00F0FF]">⟳</span> Weekly rankings • Resets Monday
      </p>
      {placeholderRows.map((rank) => (
        <div key={rank} className="leaderboard-row">
          <span className={`leaderboard-rank ${rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? 'bronze' : ''}`}>
            #{rank}
          </span>
          <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm ml-2 bg-[#1a1a1a] border border-[#333]">
            <span className="text-[#444]">-</span>
          </div>
          <div className="flex-1 ml-3">
            <p className="text-[#444]">—</p>
          </div>
          <div className="font-space text-xl text-[#333]">
            —
          </div>
        </div>
      ))}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full mt-3 py-2 text-xs text-[#00F0FF] flex items-center justify-center gap-1 hover:bg-[#1A1A1A] rounded transition-colors border border-[#262626]"
        data-testid="leaderboard-expand-btn"
      >
        {expanded ? (
          <>Show Less <ChevronUp className="w-4 h-4" /></>
        ) : (
          <>View All 10 <ChevronDown className="w-4 h-4" /></>
        )}
      </button>
    </div>
  );
};

export const BadgesDisplay = ({ badges }) => {
  if (!badges || badges.length === 0) return null;
  
  return (
    <div className="flex flex-wrap gap-1">
      {badges.map((badge, idx) => (
        <div
          key={idx}
          className="bg-[#1A1A1A] px-2 py-1 text-xs flex items-center gap-1 border border-[#262626]"
          title={badge.description || badge.id}
          style={{ borderColor: badge.color || "#262626" }}
        >
          <span>{badge.icon || BADGE_ICONS[badge.id] || "🏅"}</span>
          <span style={{ color: badge.color }}>{badge.name || badge.id}</span>
        </div>
      ))}
    </div>
  );
};