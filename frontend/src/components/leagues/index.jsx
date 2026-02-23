import { useState, useEffect, useRef } from "react";
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
  
  const shareUrl = `${window.location.origin}?joinLeague=${league.code}`;
  const shareText = `Join my Celebrity Buzz league "${league.name}"! Use code: ${league.code} 🌟`;
  
  useEffect(() => {
    fetchLeagueData();
  }, [league.id]);
  
  useEffect(() => {
    if (activeTab === "chat") {
      fetchChatMessages();
      // Poll for new messages every 10 seconds when chat is open
      const interval = setInterval(fetchChatMessages, 10000);
      return () => clearInterval(interval);
    }
  }, [activeTab, league.id]);
  
  useEffect(() => {
    // Scroll to bottom when new messages arrive
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages]);
  
  const fetchChatMessages = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/league/${league.id}/chat`);
      if (res.ok) {
        const data = await res.json();
        setChatMessages(data.messages || []);
      }
    } catch (e) {
      console.error("Error fetching chat:", e);
    }
  };
  
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
  
  const fetchLeagueData = async () => {
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
  };
  
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
  
  const currentLeaderboard = activeTab === "weekly" 
    ? (weeklyData?.leaderboard || leaderboard)
    : (monthlyData?.leaderboard || []);
  
  const pointsKey = activeTab === "weekly" ? "weekly_points" : "monthly_points";
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#0A0A0A] border border-[#262626] max-w-lg w-full max-h-[85vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="font-anton text-2xl uppercase text-[#FFD700]">{league.name}</h3>
              <p className="text-xs text-[#A1A1AA] flex items-center gap-1">
                <Users className="w-3 h-3" />
                {league.team_ids?.length || 0}/10 friends
              </p>
            </div>
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
                className="flex-1 min-w-[60px] bg-[#262626] text-white py-2 text-xs font-bold uppercase flex items-center justify-center gap-1"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? "Copied!" : "Copy"}
              </button>
              <button
                onClick={handleWhatsAppShare}
                className="flex-1 min-w-[60px] bg-[#25D366] text-white py-2 text-xs font-bold uppercase"
              >
                WhatsApp
              </button>
              <button
                onClick={handleXShare}
                className="flex-1 min-w-[60px] bg-black border border-white text-white py-2 text-xs font-bold uppercase"
              >
                𝕏
              </button>
              <button
                onClick={handleFacebookShare}
                className="flex-1 min-w-[60px] bg-[#1877F2] text-white py-2 text-xs font-bold uppercase flex items-center justify-center gap-1"
              >
                <Facebook className="w-3 h-3" />
              </button>
            </div>
          </div>
          
          {/* Weekly/Monthly/Chat Tabs */}
          <div className="flex mb-4 bg-[#1A1A1A]">
            <button
              onClick={() => setActiveTab("weekly")}
              className={`flex-1 py-3 text-xs font-bold uppercase flex items-center justify-center gap-2 transition-colors ${
                activeTab === "weekly" 
                  ? "bg-[#FF0099] text-white" 
                  : "text-[#A1A1AA] hover:text-white"
              }`}
            >
              <Calendar className="w-4 h-4" />
              Weekly
            </button>
            <button
              onClick={() => setActiveTab("monthly")}
              className={`flex-1 py-3 text-xs font-bold uppercase flex items-center justify-center gap-2 transition-colors ${
                activeTab === "monthly" 
                  ? "bg-[#00F0FF] text-black" 
                  : "text-[#A1A1AA] hover:text-white"
              }`}
            >
              <CalendarDays className="w-4 h-4" />
              Monthly
            </button>
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex-1 py-3 text-xs font-bold uppercase flex items-center justify-center gap-2 transition-colors ${
                activeTab === "chat" 
                  ? "bg-[#FFD700] text-black" 
                  : "text-[#A1A1AA] hover:text-white"
              }`}
            >
              <MessageCircle className="w-4 h-4" />
              Chat
            </button>
          </div>
          
          {/* Chat Tab Content */}
          {activeTab === "chat" ? (
            <div className="flex flex-col h-[400px]">
              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto bg-[#1A1A1A] p-3 space-y-3 mb-3">
                {chatMessages.length === 0 ? (
                  <p className="text-center text-[#666] py-8">No messages yet. Start the banter! 🔥</p>
                ) : (
                  chatMessages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex gap-2 ${msg.team_id === teamId ? 'flex-row-reverse' : ''}`}
                    >
                      <div
                        className={`max-w-[80%] p-2 rounded ${
                          msg.team_id === teamId 
                            ? 'bg-[#FF0099]/30 border border-[#FF0099]' 
                            : 'bg-[#262626]'
                        }`}
                      >
                        <p className="text-xs font-bold mb-1" style={{ color: TEAM_COLORS[msg.team_color] || "#00F0FF" }}>
                          {msg.team_name}
                          {msg.team_id === league.owner_team_id && <Crown className="w-3 h-3 inline ml-1 text-[#FFD700]" />}
                        </p>
                        <p className="text-sm">{msg.message}</p>
                        <p className="text-xs text-[#666] mt-1">
                          {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </p>
                      </div>
                    </div>
                  ))
                )}
                <div ref={chatEndRef} />
              </div>
              
              {/* Chat Input */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Talk trash..."
                  className="flex-1 bg-[#1A1A1A] border border-[#262626] p-2 text-sm text-white"
                  maxLength={500}
                  disabled={!teamId}
                />
                <button
                  onClick={sendMessage}
                  disabled={!newMessage.trim() || sendingMessage || !teamId}
                  className="bg-[#FFD700] text-black px-4 py-2 font-bold uppercase text-xs disabled:opacity-50 flex items-center gap-1"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              {!teamId && (
                <p className="text-xs text-[#FF0099] mt-2">Create a team to join the chat!</p>
              )}
            </div>
          ) : (
            <>
              {/* Leaderboard */}
              <h4 className="font-anton text-lg uppercase text-[#00F0FF] mb-3 flex items-center gap-2">
                <Trophy className="w-5 h-5" />
                {activeTab === "weekly" ? "This Week's Standings" : "Monthly Standings"}
              </h4>
              
              {loading ? (
                <div className="text-center py-8 text-[#A1A1AA]">Loading...</div>
              ) : currentLeaderboard.length > 0 ? (
                <div className="space-y-2">
                  {currentLeaderboard.map((entry, idx) => (
                    <div
                      key={entry.team_id}
                      className={`flex items-center gap-3 p-3 ${
                        entry.team_id === teamId 
                          ? 'bg-[#FF0099]/20 border border-[#FF0099]' 
                          : 'bg-[#1A1A1A]'
                      }`}
                    >
                      {/* Rank */}
                      <span className={`font-anton text-xl w-8 ${
                        idx === 0 ? 'text-[#FFD700]' 
                        : idx === 1 ? 'text-[#C0C0C0]' 
                        : idx === 2 ? 'text-[#CD7F32]' 
                        : 'text-[#666]'
                      }`}>
                        #{idx + 1}
                  </span>
                  
                  {/* Team Info */}
                  <div className="flex-1">
                    <p className="font-bold text-sm flex items-center gap-2 flex-wrap">
                      {entry.team_name}
                      {entry.is_owner && <Crown className="w-3 h-3 text-[#FFD700]" />}
                      {/* Show badges */}
                      {entry.badges?.slice(0, 3).map((badgeId, i) => (
                        <span key={i} className="text-sm" title={badgeId}>
                          {BADGE_ICONS[badgeId] || "🏅"}
                        </span>
                      ))}
                    </p>
                    <p className="text-xs text-[#A1A1AA]">{entry.celebrity_count} celebs</p>
                  </div>
                  
                  {/* Points */}
                  <span className="font-space font-bold text-[#FF0099] text-lg">
                    {(entry[pointsKey] || entry.total_points || 0).toFixed(1)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-[#666] py-4">No teams yet!</p>
          )}
          
          {/* Recent Winners */}
          {activeTab === "weekly" && weeklyData?.weekly_winner_history?.length > 0 && (
            <div className="mt-6">
              <h5 className="font-anton text-sm uppercase text-[#A1A1AA] mb-2">Recent Winners</h5>
              <div className="flex gap-2 flex-wrap">
                {weeklyData.weekly_winner_history.slice(-4).reverse().map((winner, i) => (
                  <div key={i} className="bg-[#1A1A1A] px-3 py-2 text-xs">
                    <span className="text-[#FFD700]">🏆</span> {winner.team_name}
                    <span className="text-[#666] ml-1">({winner.week})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {activeTab === "monthly" && monthlyData?.monthly_winner_history?.length > 0 && (
            <div className="mt-6">
              <h5 className="font-anton text-sm uppercase text-[#A1A1AA] mb-2">Monthly Champions</h5>
              <div className="flex gap-2 flex-wrap">
                {monthlyData.monthly_winner_history.slice(-3).reverse().map((winner, i) => (
                  <div key={i} className="bg-[#1A1A1A] px-3 py-2 text-xs">
                    <span className="text-[#FF0099]">🌟</span> {winner.team_name}
                    <span className="text-[#666] ml-1">({winner.month})</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* League Stats */}
          {stats && (
            <div className="mt-6 pt-4 border-t border-[#262626]">
              <h5 className="font-anton text-sm uppercase text-[#A1A1AA] mb-3 flex items-center gap-2">
                <Award className="w-4 h-4" />
                League Stats
              </h5>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-[#1A1A1A] p-2">
                  <p className="text-[#666]">Weeks Played</p>
                  <p className="font-bold text-[#00F0FF]">{stats.weeks_played || 0}</p>
                </div>
                <div className="bg-[#1A1A1A] p-2">
                  <p className="text-[#666]">Total Celebs</p>
                  <p className="font-bold text-[#FF0099]">{stats.total_celebrities_drafted || 0}</p>
                </div>
                {stats.most_decorated_team?.team_name && (
                  <div className="bg-[#1A1A1A] p-2 col-span-2">
                    <p className="text-[#666]">Most Decorated</p>
                    <p className="font-bold text-[#FFD700]">
                      {stats.most_decorated_team.team_name} ({stats.most_decorated_team.badge_count} badges)
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Leaderboard Component (Global)
export const Leaderboard = ({ entries }) => {
  const [expanded, setExpanded] = useState(false);
  
  // Desktop always shows 10, mobile shows 5 collapsed / 10 expanded
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
  const displayCount = isMobile ? (expanded ? 10 : 5) : 10;
  const placeholderRows = Array.from({ length: displayCount }, (_, i) => i + 1);
  
  return (
    <div className="leaderboard" data-testid="leaderboard">
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
      
      {/* Expand/Collapse button - MOBILE ONLY */}
      {isMobile && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 py-2 text-xs text-[#00F0FF] flex items-center justify-center gap-1 hover:bg-[#1A1A1A] rounded transition-colors border border-[#262626]"
          data-testid="leaderboard-expand-btn"
        >
          {expanded ? (
            <>Show Top 5 <ChevronUp className="w-4 h-4" /></>
          ) : (
            <>View All 10 <ChevronDown className="w-4 h-4" /></>
          )}
        </button>
      )}
    </div>
  );
};

// Badges Display Component
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
