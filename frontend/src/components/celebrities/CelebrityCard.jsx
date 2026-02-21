import { useState, useEffect } from "react";
import { Film, Tv, Music, Trophy, Crown, Star, Users, LineChart, Sparkles } from "lucide-react";
import TierBadge from "../common/TierBadge";
import { getAiImage } from "../../api";

const categoryIcons = {
  movie_stars: Film,
  tv_actors: Tv,
  musicians: Music,
  athletes: Trophy,
  royals: Crown,
  reality_tv: Star,
  other: Users,
};

// Check if image is a placeholder (ui-avatars)
const isPlaceholderImage = (url) => {
  return !url || url.includes("ui-avatars.com");
};

const CelebrityCard = ({ celebrity, onAdd, isInTeam, canAfford, onShowPriceHistory }) => {
  const [showNews, setShowNews] = useState(false);
  const [imageUrl, setImageUrl] = useState(celebrity.image);
  const [isGeneratingAi, setIsGeneratingAi] = useState(false);
  const [hasAiImage, setHasAiImage] = useState(false);
  const Icon = categoryIcons[celebrity.category] || Star;
  
  // Check for AI image if current image is a placeholder
  useEffect(() => {
    const checkForAiImage = async () => {
      if (isPlaceholderImage(celebrity.image) && !hasAiImage) {
        try {
          // Check if we have a cached AI image
          const result = await getAiImage(celebrity.name);
          if (result.image && !result.image.includes("ui-avatars.com")) {
            setImageUrl(result.image);
            setHasAiImage(true);
          }
        } catch (e) {
          // Silently fail - keep placeholder
        }
      }
    };
    
    checkForAiImage();
  }, [celebrity.name, celebrity.image, hasAiImage]);
  
  // Handle generating AI image on demand
  const handleGenerateAiImage = async (e) => {
    e.stopPropagation();
    if (isGeneratingAi) return;
    
    setIsGeneratingAi(true);
    try {
      const result = await getAiImage(celebrity.name);
      if (result.image && !result.image.includes("ui-avatars.com")) {
        setImageUrl(result.image);
        setHasAiImage(true);
      }
    } catch (error) {
      console.error("Failed to generate AI image:", error);
    } finally {
      setIsGeneratingAi(false);
    }
  };
  
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
          src={imageUrl || `https://ui-avatars.com/api/?name=${celebrity.name}&size=400&background=FF0099&color=fff`}
          alt={celebrity.name}
          className="celebrity-card-image"
          onError={(e) => {
            e.target.src = `https://ui-avatars.com/api/?name=${celebrity.name}&size=400&background=FF0099&color=fff`;
          }}
        />
        
        {/* AI Generate button for placeholder images */}
        {isPlaceholderImage(imageUrl) && !hasAiImage && (
          <button
            onClick={handleGenerateAiImage}
            disabled={isGeneratingAi}
            className="absolute bottom-3 left-3 bg-gradient-to-r from-[#8B5CF6] to-[#FF0099] text-white px-2 py-1 text-[10px] font-bold flex items-center gap-1 hover:opacity-90 transition-opacity disabled:opacity-50"
            title="Generate AI portrait"
            data-testid={`ai-gen-btn-${celebrity.id}`}
          >
            <Sparkles className="w-3 h-3" />
            {isGeneratingAi ? "Generating..." : "AI Photo"}
          </button>
        )}
        
        {/* AI badge if image was AI generated */}
        {hasAiImage && (
          <div className="absolute bottom-3 left-3 bg-[#8B5CF6]/80 text-white px-2 py-0.5 text-[8px] font-bold flex items-center gap-1">
            <Sparkles className="w-2.5 h-2.5" />
            AI Generated
          </div>
        )}
        
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
