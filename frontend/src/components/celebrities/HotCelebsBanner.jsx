import { TrendingUp } from "lucide-react";
import TierBadge from "../common/TierBadge";

const HotCelebsBanner = ({ celebs, onSelect }) => {
  if (!celebs || celebs.length === 0) return null;
  
  // Double the celebs for infinite scroll effect
  const doubledCelebs = [...celebs, ...celebs];
  
  return (
    <div className="bg-gradient-to-r from-[#FF0099]/30 via-[#0A0A0A] to-[#00F0FF]/30 border-b border-[#FF0099]/50 p-4 overflow-hidden" data-testid="hot-celebs-banner">
      <div className="max-w-7xl mx-auto">
        <h3 className="font-anton text-lg uppercase tracking-tight text-white mb-3 flex items-center gap-2">
          🔥 Hot Celebs This Week
          <span className="text-xs font-normal text-[#A1A1AA]">(prices increase with news coverage)</span>
        </h3>
        <div className="hot-celebs-scroll-container">
          <div className="hot-celebs-scroll-content">
            {doubledCelebs.map((celeb, idx) => (
              <div 
                key={idx}
                onClick={() => onSelect(celeb.name)}
                className="flex-shrink-0 w-28 bg-[#1A1A1A] border border-[#262626] p-2 cursor-pointer hover:border-[#FF0099] transition-colors group"
              >
                <div className="relative mb-1">
                  <img 
                    src={celeb.image} 
                    alt={celeb.name}
                    className="w-full h-20 object-cover"
                    onError={(e) => { e.target.src = `https://ui-avatars.com/api/?name=${celeb.name}&size=128&background=FF0099&color=fff`; }}
                  />
                  <div className={`absolute top-0 right-0 px-1 py-0.5 text-[7px] font-bold ${
                    celeb.tier === 'A' ? 'bg-[#FFD700] text-black' : celeb.tier === 'B' ? 'bg-[#C0C0C0] text-black' : celeb.tier === 'C' ? 'bg-[#CD7F32] text-white' : 'bg-[#666] text-white'
                  }`}>
                    {celeb.tier}-LIST
                  </div>
                  {celeb.trending_tag && (
                    <div className="absolute top-0 left-0 text-[10px]">
                      {celeb.trending_tag}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <p className="font-bold text-xs text-white truncate group-hover:text-[#FF0099] flex-1">{celeb.name}</p>
                  {celeb.news_premium && (
                    <TrendingUp className="w-3 h-3 text-[#00FF00] flex-shrink-0" />
                  )}
                </div>
                <p className={`text-[10px] font-bold ${celeb.news_premium ? 'text-[#00FF00]' : 'text-[#00FF00]'}`}>
                  £{celeb.price}M
                  {celeb.news_premium && <span className="text-[8px] ml-1 text-[#00FF00]">▲</span>}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default HotCelebsBanner;
