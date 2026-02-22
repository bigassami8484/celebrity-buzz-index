import { Users } from "lucide-react";

const Footer = ({ playerCount }) => (
  <footer className="bg-[#050505] border-t border-[#262626] py-8 mt-16" data-testid="footer">
    <div className="max-w-7xl mx-auto px-4 text-center">
      {/* Player Count */}
      <div className="flex items-center justify-center gap-2 mb-6">
        <div className="bg-[#FF0099]/20 border border-[#FF0099] px-6 py-3 inline-flex items-center gap-3">
          <Users className="w-5 h-5 text-[#FF0099]" />
          <div>
            <span className="text-2xl font-bold text-white">{playerCount?.toLocaleString() || 0}</span>
            <span className="text-sm text-[#A1A1AA] ml-2">Players</span>
          </div>
        </div>
      </div>
      
      <p className="text-sm text-[#A1A1AA] mb-4">
        Celebrity Buzz Index scores are calculated automatically based on media mentions and do not reflect personal opinions.
      </p>
      <p className="text-xs text-[#666]">
        © 2026 Celebrity Buzz Index. All rights reserved.
      </p>
    </div>
  </footer>
);

export default Footer;
