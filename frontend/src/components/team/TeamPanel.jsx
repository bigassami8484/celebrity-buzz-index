import { useState } from "react";
import { Minus, Share2, Lock, Unlock, TrendingUp, TrendingDown, Zap } from "lucide-react";

// Helper to calculate price change
const getPriceChange = (current, previous) => {
  if (!previous || previous === 0) return null;
  const diff = current - previous;
  if (Math.abs(diff) < 0.1) return null;
  const percent = ((diff / previous) * 100).toFixed(0);
  // Format the money difference
  const moneyDiff = diff >= 1 ? `£${diff.toFixed(1)}M` : `£${(diff * 1000).toFixed(0)}K`;
  return { diff, percent, moneyDiff };
};

const TeamPanel = ({ team, onRemove, onShare, onCustomize, onSubmitTeam, isTransferWindowOpen }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  if (!team) return null;
  
  const isTeamLocked = team.is_locked && !isTransferWindowOpen;
  const canEdit = !isTeamLocked || isTransferWindowOpen;
  
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
      {/* Team Lock Status */}
      {isTeamLocked && (
        <div className="bg-red-500/10 border border-red-500/50 p-2 mb-4 flex items-center justify-center gap-2 text-xs">
          <Lock className="w-3 h-3 text-red-400" />
          <span className="text-red-400">Team locked until transfer window (Saturday)</span>
        </div>
      )}
      {isTransferWindowOpen && (
        <div className="bg-green-500/10 border border-green-500/50 p-2 mb-4 flex items-center justify-center gap-2 text-xs">
          <Unlock className="w-3 h-3 text-green-400" />
          <span className="text-green-400 font-bold">Transfer window OPEN! Make changes now.</span>
        </div>
      )}
      
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
              {team.celebrities?.length || 0}/10 celebrities • £{(team.budget_remaining || 50).toFixed(1)}M remaining
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
          {team.celebrities.map((celeb) => {
            const priceChange = getPriceChange(celeb.price, celeb.previous_week_price);
            const dailyPoints = celeb.daily_points || 0;
            return (
            <div key={celeb.celebrity_id} className={`team-celeb ${isTeamLocked ? 'opacity-80' : ''}`} data-testid={`team-celeb-${celeb.celebrity_id}`}>
              <img 
                src={celeb.image || `https://ui-avatars.com/api/?name=${celeb.name}&size=100&background=FF0099&color=fff`} 
                alt={celeb.name}
                className="team-celeb-image"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <p className="font-bold">
                    {celeb.name}
                    {celeb.is_deceased && <span className="ml-1" title="Deceased">💀</span>}
                  </p>
                  {dailyPoints > 0 && (
                    <span className="flex items-center gap-1 text-xs font-bold text-[#00F0FF] bg-[#00F0FF]/10 px-2 py-0.5 rounded-full">
                      <Zap className="w-3 h-3" />
                      +{dailyPoints.toFixed(1)}
                    </span>
                  )}
                </div>
                <p className="text-sm text-[#A1A1AA] flex items-center gap-2">
                  <span className="text-[#FFD700]">£{celeb.price}M</span>
                  {priceChange && (
                    <span className={`flex items-center gap-0.5 text-xs font-bold ${priceChange.diff > 0 ? 'text-green-400' : 'text-red-400'}`} title={`Transfer value: ${priceChange.diff > 0 ? '+' : ''}${priceChange.moneyDiff}`}>
                      {priceChange.diff > 0 ? (
                        <TrendingUp className="w-3 h-3" />
                      ) : (
                        <TrendingDown className="w-3 h-3" />
                      )}
                      {priceChange.diff > 0 ? '+' : ''}{priceChange.moneyDiff}
                    </span>
                  )}
                </p>
              </div>
              {canEdit ? (
                <button 
                  onClick={() => onRemove(celeb.celebrity_id)}
                  className="remove-btn"
                  data-testid={`remove-btn-${celeb.celebrity_id}`}
                >
                  <Minus className="w-5 h-5" />
                </button>
              ) : (
                <Lock className="w-5 h-5 text-[#666]" />
              )}
            </div>
          )})}
          
          {/* Submit Team / Share Buttons */}
          <div className="flex gap-2 mt-4">
            {!team.is_locked && team.celebrities?.length >= 5 && (
              <button 
                onClick={async () => {
                  setIsSubmitting(true);
                  await onSubmitTeam?.();
                  setIsSubmitting(false);
                }}
                disabled={isSubmitting}
                className="flex-1 bg-gradient-to-r from-[#FF0099] to-[#FF6600] text-white font-bold py-3 px-4 rounded flex items-center justify-center gap-2 hover:opacity-90 transition-opacity disabled:opacity-50"
                data-testid="submit-team-btn"
              >
                <Lock className="w-4 h-4" />
                {isSubmitting ? 'Submitting...' : 'Submit & Lock Team'}
              </button>
            )}
            <button 
              onClick={onShare}
              className={`${!team.is_locked && team.celebrities?.length >= 5 ? 'flex-1' : 'w-full'} add-button flex items-center justify-center gap-2`}
              data-testid="share-team-btn"
            >
              <Share2 className="w-4 h-4" />
              Share Team
            </button>
          </div>
        </>
      ) : (
        <p className="text-center text-[#A1A1AA] py-8">
          Search and add celebrities to build your team!
        </p>
      )}
    </div>
  );
};

export default TeamPanel;
