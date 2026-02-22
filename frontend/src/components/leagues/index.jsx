import { useState } from "react";
import { Trophy, Crown, X, Copy, Check, Facebook } from "lucide-react";
import { toast } from "sonner";

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
export const LeagueDetailModal = ({ league, leaderboard, onClose, teamId }) => {
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

// Leaderboard Component
export const Leaderboard = ({ entries }) => {
  // Create placeholder rows 1-10 - show empty until real players join
  const placeholderRows = Array.from({ length: 10 }, (_, i) => i + 1);
  
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
          {/* Empty placeholder - waiting for players */}
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
    </div>
  );
};
