import { TrendingUp } from "lucide-react";

const TopPickedCelebs = ({ celebs, onSelect }) => {
  if (!celebs || celebs.length === 0) return null;
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 h-full" data-testid="top-picked">
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

export default TopPickedCelebs;
