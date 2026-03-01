import { Newspaper } from "lucide-react";

const TodaysNews = ({ news }) => {
  if (!news || news.length === 0) return null;
  
  return (
    <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-4" data-testid="todays-news">
      <h3 className="font-anton text-lg uppercase tracking-tight text-[#FF0099] mb-3 flex items-center gap-2">
        <Newspaper className="w-5 h-5" />
        Celeb News
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {news.slice(0, 6).map((item, idx) => (
          <a 
            key={idx} 
            href={item.url || "#"} 
            target="_blank" 
            rel="noopener noreferrer"
            className="bg-[#1A1A1A] p-2 hover:bg-[#222] transition-colors block group"
          >
            <p className="text-[10px] text-[#00F0FF] uppercase mb-1">{item.source}</p>
            <p className="font-bold text-xs text-white line-clamp-3 group-hover:text-[#FF0099]">{item.headline}</p>
          </a>
        ))}
      </div>
    </div>
  );
};

export default TodaysNews;
