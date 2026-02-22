import { Skull } from "lucide-react";

const BrownBreadWatch = ({ watchList, onSelect }) => {
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
              <span className="text-sm truncate block">
                {celeb.name}
                {celeb.is_deceased && <span className="ml-1" title="Deceased">💀</span>}
              </span>
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

export default BrownBreadWatch;
