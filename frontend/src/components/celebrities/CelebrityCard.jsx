import { useState } from "react";
import { Film, Tv, Music, Trophy, Crown, Star, Users, LineChart, TrendingUp, TrendingDown, Minus } from "lucide-react";
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

// Price change indicator component - uses dark colors for visibility on yellow background
const PriceChangeIndicator = ({ currentPrice, previousPrice }) => {
  if (!previousPrice || previousPrice === 0) return null;
  
  const diff = currentPrice - previousPrice;
  const percentChange = ((diff / previousPrice) * 100).toFixed(0);
  
  if (Math.abs(diff) < 0.1) {
    return (
      <span className="flex items-center gap-0.5 text-[#666] text-xs">
        <Minus className="w-3 h-3" />
      </span>
    );
  }
  
  if (diff > 0) {
    return (
      <span className="flex items-center gap-0.5 text-emerald-700 text-xs font-bold">
        <TrendingUp className="w-3 h-3" />
        +{percentChange}%
      </span>
    );
  }
  
  return (
    <span className="flex items-center gap-0.5 text-red-700 text-xs font-bold">
      <TrendingDown className="w-3 h-3" />
      {percentChange}%
    </span>
  );
};

const CelebrityCard = ({ celebrity, onAdd, onRemove, isInTeam, canAfford, onShowPriceHistory, compact = false }) => {
  const [showNews, setShowNews] = useState(false);
  const Icon = categoryIcons[celebrity.category] || Star;
  
  // Compact mobile version with news and wiki
  if (compact) {
    return (
      <div className="bg-[#0A0A0A] border border-[#262626] rounded-lg overflow-hidden" data-testid={`celebrity-card-${celebrity.id}`}>
        <div className="relative">
          <img
            src={celebrity.image || `https://ui-avatars.com/api/?name=${celebrity.name}&size=200&background=FF0099&color=fff`}
            alt={celebrity.name}
            className="w-full h-28 object-cover"
            onError={(e) => {
              e.target.src = `https://ui-avatars.com/api/?name=${celebrity.name}&size=200&background=FF0099&color=fff`;
            }}
          />
          <div className="absolute top-2 left-2">
            <TierBadge tier={celebrity.tier || "D"} />
          </div>
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 to-transparent p-2">
            <h3 className="font-bold text-white text-xs truncate">{celebrity.name}</h3>
          </div>
        </div>
        <div className="p-2">
          {/* Price with arrows */}
          <div className="flex items-center justify-between mb-1">
            <span className="text-[#FFD700] font-bold text-sm">£{celebrity.price}M</span>
            <PriceChangeIndicator currentPrice={celebrity.price} previousPrice={celebrity.previous_week_price} />
          </div>
          
          {/* Latest news - compact */}
          {celebrity.news?.length > 0 && (
            <div className="mb-2 text-[10px] text-[#A1A1AA] truncate">
              📰 {celebrity.news[0]?.title?.slice(0, 40)}...
            </div>
          )}
          
          {/* Wiki link */}
          {celebrity.wiki_url && (
            <a 
              href={celebrity.wiki_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="block text-[10px] text-[#00F0FF] mb-2 truncate"
              onClick={(e) => e.stopPropagation()}
            >
              Wikipedia →
            </a>
          )}
          
          {isInTeam ? (
            <button
              onClick={() => onRemove && onRemove(celebrity.id)}
              className="w-full py-1.5 text-xs font-bold rounded transition-colors bg-red-600 text-white hover:bg-red-700"
              data-testid={`remove-btn-${celebrity.id}`}
            >
              Remove
            </button>
          ) : (
            <button
              onClick={() => onAdd(celebrity)}
              disabled={!canAfford}
              className={`w-full py-1.5 text-xs font-bold rounded transition-colors ${
                !canAfford ? 'bg-[#333] text-[#666]' : 
                'bg-[#FF0099] text-white hover:bg-[#e6008a]'
              }`}
              data-testid={`add-btn-${celebrity.id}`}
            >
              {!canAfford ? "Can't Afford" : "Add"}
            </button>
          )}
        </div>
      </div>
    );
  }
  
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
        {/* Bottom overlay - name, category, price */}
        <div className="celebrity-card-overlay">
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="category-badge flex items-center gap-1">
              <Icon className="w-3 h-3" />
              {celebrity.category?.replace("_", " ")}
            </span>
            <span className="price-tag flex items-center gap-1">
              £{celebrity.price}M
              <PriceChangeIndicator 
                currentPrice={celebrity.price} 
                previousPrice={celebrity.previous_week_price} 
              />
            </span>
          </div>
          <h3 className="font-anton text-xl uppercase tracking-tight leading-tight">
            {celebrity.name}
            {celebrity.is_deceased && <span className="ml-2" title="Deceased">💀</span>}
          </h3>
          {/* Bio - smaller text, limited to 2 lines */}
          <p className="text-xs text-[#A1A1AA]/80 line-clamp-2 mt-1 leading-snug">{celebrity.bio?.slice(0, 100)}</p>
          {celebrity.wiki_url && (
            <a 
              href={celebrity.wiki_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-[#00F0FF] hover:underline mt-1 inline-block"
              onClick={(e) => e.stopPropagation()}
            >
              Wikipedia →
            </a>
          )}
        </div>
        
        {/* News Panel on Hover */}
        <div className={`news-panel ${showNews ? 'opacity-100' : ''}`}>
          <h4 className="font-anton text-lg uppercase mb-4 text-[#00F0FF]">Latest News</h4>
          {celebrity.news?.length > 0 ? (
            celebrity.news.slice(0, 4).map((item, idx) => (
              <a 
                key={idx} 
                href={item.url || `https://www.google.com/search?q=${encodeURIComponent(item.title + ' ' + item.source)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="news-item block hover:bg-[#262626] transition-colors cursor-pointer"
                onClick={(e) => e.stopPropagation()}
              >
                <p className="news-title hover:text-[#FF0099] transition-colors">{item.title}</p>
                <p className="news-source">
                  {item.source} • {item.date}
                  {item.is_real && <span className="text-green-400 ml-1" title="Real news">✓</span>}
                </p>
              </a>
            ))
          ) : (
            <p className="text-[#A1A1AA] text-sm">No recent news stories</p>
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
