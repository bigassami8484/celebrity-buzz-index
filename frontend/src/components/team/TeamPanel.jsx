import { useState } from "react";
import { Minus, Share2, RotateCcw } from "lucide-react";

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
      {/* Weekly Reset Notice */}
      <div className="bg-[#1A1A1A] border border-[#262626] p-2 mb-4 flex items-center justify-center gap-2 text-xs">
        <RotateCcw className="w-3 h-3 text-[#00F0FF]" />
        <span className="text-[#A1A1AA]">Points reset every <span className="text-[#FFD700] font-bold">Monday</span> at midnight GMT</span>
      </div>
      
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
              {team.celebrities?.length || 0} celebrities • {team.total_points?.toFixed(1)} weekly pts
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

export default TeamPanel;
