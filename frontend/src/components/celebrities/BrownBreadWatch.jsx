import { useState } from "react";
import { Skull, ChevronDown, ChevronUp, Plus } from "lucide-react";

const BrownBreadWatch = ({ watchList, onSelect, onAdd }) => {
  const [expanded, setExpanded] = useState(false);
  
  if (!watchList || watchList.length === 0) return null;
  
  const getRiskEmoji = (risk) => {
    switch(risk) {
      case 'critical': return '🔴';
      case 'high': return '🟠';
      case 'elevated': return '🟡';
      case 'moderate': return '🟢';
      default: return '⚪';
    }
  };
  
  // Show 5 items to match other panels
  const displayList = expanded ? watchList.slice(0, 10) : watchList.slice(0, 5);
  const hasMore = watchList.length > 5;
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 h-full" data-testid="brown-bread-watch">
      <h4 className="font-anton text-lg uppercase tracking-tight text-[#888] mb-3 flex items-center gap-2">
        <Skull className="w-5 h-5" />
        Brown Bread Watch
      </h4>
      <p className="text-xs text-[#666] mb-3">Strategic picks for the +100 bonus 💀</p>
      <div className="space-y-2">
        {displayList.map((celeb, idx) => (
          <div 
            key={celeb.id} 
            className={`flex items-center gap-2 p-2 hover:bg-[#1A1A1A] group ${celeb.is_premium ? 'border-l-2 border-[#FFD700] bg-[#FFD700]/5' : ''}`}
          >
            <span className="text-lg" title={`Risk: ${celeb.risk_level}`}>
              {getRiskEmoji(celeb.risk_level)}
            </span>
            <img 
              src={celeb.image} 
              alt={celeb.name}
              className="w-8 h-8 rounded-full object-cover grayscale cursor-pointer"
              onClick={() => onSelect(celeb.name)}
              onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=32&background=666&color=fff`; }}
            />
            <div className="flex-1 min-w-0 cursor-pointer" onClick={() => onSelect(celeb.name)}>
              <span className="text-sm truncate block hover:text-[#FF0099]">
                {celeb.name} <span className="text-[#666]">({celeb.age})</span>
              </span>
            </div>
            <div className="text-right flex items-center gap-2">
              <span className={`text-sm font-bold ${celeb.is_premium ? 'text-[#FFD700]' : 'text-[#A1A1AA]'}`}>
                £{celeb.price}M
              </span>
              {onAdd && (
                <button
                  onClick={(e) => { e.stopPropagation(); onAdd(celeb); }}
                  className="opacity-0 group-hover:opacity-100 bg-[#FF0099] hover:bg-[#e6008a] text-white text-xs px-2 py-1 rounded transition-all"
                  title={`Add ${celeb.name}`}
                  data-testid={`add-brownbread-${idx}`}
                >
                  <Plus className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {/* Expand/Collapse button for mobile */}
      {hasMore && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 py-2 text-xs text-[#00F0FF] flex items-center justify-center gap-1 hover:bg-[#1A1A1A] rounded transition-colors"
          data-testid="brown-bread-expand-btn"
        >
          {expanded ? (
            <>Show Less <ChevronUp className="w-4 h-4" /></>
          ) : (
            <>View All {watchList.length} <ChevronDown className="w-4 h-4" /></>
          )}
        </button>
      )}
    </div>
  );
};

export default BrownBreadWatch;
