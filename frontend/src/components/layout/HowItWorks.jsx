import { Search, Star, Plus, ArrowLeftRight, Skull, Info, Globe } from "lucide-react";

const HowItWorks = ({ onShowMethodology }) => (
  <div className="bg-[#0A0A0A] border border-[#262626] p-4 mb-8" data-testid="how-it-works">
    <div className="flex justify-between items-center mb-3">
      <h3 className="font-anton text-lg uppercase tracking-tight text-[#FFD700]">How It Works</h3>
      <button 
        onClick={onShowMethodology}
        className="flex items-center gap-1 text-[#00F0FF] hover:text-white text-xs"
        data-testid="show-methodology-btn"
      >
        <Info className="w-3 h-3" />
        Points Info
      </button>
    </div>
    <div className="grid grid-cols-5 gap-2">
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FF0099] flex items-center justify-center mx-auto mb-2">
          <Search className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm">Search</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Find any celeb</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#00F0FF] flex items-center justify-center mx-auto mb-2">
          <Star className="w-5 h-5 text-black" />
        </div>
        <h4 className="font-space font-bold text-sm">£0.5-15M</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Tier pricing</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FFD700] flex items-center justify-center mx-auto mb-2">
          <Plus className="w-5 h-5 text-black" />
        </div>
        <h4 className="font-space font-bold text-sm">£50M</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Your budget</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#FF5500] flex items-center justify-center mx-auto mb-2">
          <ArrowLeftRight className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm">Sun 12pm</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Transfer window</p>
      </div>
      <div className="text-center">
        <div className="w-10 h-10 bg-[#8B5CF6] flex items-center justify-center mx-auto mb-2">
          <Skull className="w-5 h-5 text-white" />
        </div>
        <h4 className="font-space font-bold text-sm">+100</h4>
        <p className="text-xs text-[#A1A1AA] mt-1">Brown Bread</p>
      </div>
    </div>
    {/* Icon Legend */}
    <div className="mt-3 pt-3 border-t border-[#262626] flex justify-center text-xs text-[#A1A1AA]">
      <span className="flex items-center gap-1">
        <span className="text-cyan-400">🌍</span> = Wikipedia languages (the higher the number, the more globally famous)
      </span>
    </div>
  </div>
);

export default HowItWorks;
