import { useState } from "react";
import { Film, Tv, Music, Trophy, Crown, Star, Users, LineChart } from "lucide-react";
import TierBadge from "../common/TierBadge";

const categoryIcons = {
  movie_stars: Film,
  tv_actors: Tv,
  musicians: Music,
  athletes: Trophy,
  royals: Crown,
  reality_tv: Star,
  other: Users,
};

const CelebrityCard = ({ celebrity, onAdd, isInTeam, canAfford, onShowPriceHistory }) => {
  const [showNews, setShowNews] = useState(false);
  const Icon = categoryIcons[celebrity.category] || Star;
  
  return (
    <div 
      className="celebrity-card"
      data-testid={`celebrity-card-${celebrity.id}`}
    >
      <div 
        className="relative overflow-hidden"
        onMouseEnter={() => setShowNews(true)}
        onMouseLeave={() => setShowNews(false)}
      >
        <img
          src={celebrity.image || `https://ui-avatars.com/api/?name=${celebrity.name}&size=400&background=FF0099&color=fff`}
          alt={celebrity.name}
          className="celebrity-card-image"
          onError={(e) => {
            e.target.src = `https://ui-avatars.com/api/?name=${celebrity.name}&size=400&background=FF0099&color=fff`;
          }}
        />
        <div className="buzz-score hidden" data-testid={`buzz-score-${celebrity.id}`}>
          {celebrity.buzz_score?.toFixed(1)}
        </div>
        {/* Tier badge top left */}
        <div className="absolute top-3 left-3">
          <TierBadge tier={celebrity.tier || "D"} />
        </div>
        {/* Price history button top right */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onShowPriceHistory(celebrity.name);
          }}
          className="absolute top-3 right-3 bg-[#0A0A0A]/80 p-1.5 hover:bg-[#FF0099] transition-colors"
          title="View price history"
          data-testid={`price-history-btn-${celebrity.id}`}
        >
          <LineChart className="w-4 h-4 text-[#00F0FF]" />
        </button>
        <div className="celebrity-card-overlay">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="category-badge flex items-center gap-1">
              <Icon className="w-3 h-3" />
              {celebrity.category?.replace("_", " ")}
            </span>
            <span className="price-tag">£{celebrity.price}M</span>
          </div>
          <h3 className="font-anton text-2xl uppercase tracking-tight">{celebrity.name}</h3>
          <p className="text-sm text-[#A1A1AA] line-clamp-2 mt-1">{celebrity.bio?.slice(0, 100)}...</p>
          {celebrity.wiki_url && (
            <a 
              href={celebrity.wiki_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-[#00F0FF] hover:underline mt-2 inline-block"
              onClick={(e) => e.stopPropagation()}
            >
              View on Wikipedia →
            </a>
          )}
        </div>
        
        {/* News Panel on Hover */}
        <div className={`news-panel ${showNews ? 'opacity-100' : ''}`}>
          <h4 className="font-anton text-lg uppercase mb-4 text-[#00F0FF]">Latest News</h4>
          {celebrity.news?.length > 0 ? (
            celebrity.news.slice(0, 4).map((item, idx) => (
              <div key={idx} className="news-item">
                <p className="news-title">{item.title}</p>
                <p className="news-source">{item.source} • {item.date}</p>
              </div>
            ))
          ) : (
            <p className="text-[#A1A1AA] text-sm">No recent news available</p>
          )}
        </div>
      </div>
      
      {/* Button outside of hover zone */}
      <div className="p-4 bg-[#0A0A0A]">
        <button
          onClick={() => onAdd(celebrity)}
          disabled={isInTeam || !canAfford}
          className="add-button"
          data-testid={`add-btn-${celebrity.id}`}
        >
          {isInTeam ? "In Team" : !canAfford ? "Can't Afford" : "Add to Team"}
        </button>
      </div>
    </div>
  );
};

export default CelebrityCard;
