import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

const Terms = () => {
  return (
    <div className="min-h-screen bg-[#050505] text-white">
      <div className="max-w-3xl mx-auto px-6 py-12">
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-[#A1A1AA] hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft size={20} />
          Back to Home
        </Link>
        
        <h1 className="font-anton text-4xl md:text-5xl uppercase mb-8">
          <span className="text-[#FF0099]">Terms</span> & <span className="text-[#00F0FF]">Conditions</span>
        </h1>
        
        <div className="space-y-8 text-[#E5E5E5]">
          <section>
            <h2 className="text-xl font-bold text-white mb-3">Data Sources</h2>
            <p className="leading-relaxed">
              Data displayed on this platform is derived from publicly available sources including Wikipedia and other open data repositories.
            </p>
          </section>
          
          <section>
            <h2 className="text-xl font-bold text-white mb-3">Rankings</h2>
            <p className="leading-relaxed">
              All celebrity rankings and tier classifications are algorithmically generated based on publicly available metrics. These rankings are for entertainment purposes only and do not represent official endorsements or valuations.
            </p>
          </section>
          
          <section>
            <h2 className="text-xl font-bold text-white mb-3">Trademarks</h2>
            <p className="leading-relaxed">
              All trademarks, service marks, trade names, and logos displayed on this platform belong to their respective owners. The use of any trademark does not imply endorsement by the trademark owner.
            </p>
          </section>
        </div>
        
        <div className="mt-12 pt-8 border-t border-[#262626] text-[#A1A1AA] text-sm">
          <p>Last updated: February 2026</p>
        </div>
      </div>
    </div>
  );
};

export default Terms;
