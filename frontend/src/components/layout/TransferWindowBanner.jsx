import { useState, useEffect } from "react";
import { Clock } from "lucide-react";

const TransferWindowBanner = ({ stats }) => {
  const [countdown, setCountdown] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  
  useEffect(() => {
    if (!stats?.transfer_window) return;
    
    const updateCountdown = () => {
      const now = new Date();
      
      // Calculate if window is open (Saturday 12pm GMT to Sunday 12pm GMT)
      const utcDay = now.getUTCDay();
      const utcHour = now.getUTCHours();
      const utcMinutes = now.getUTCMinutes();
      const utcSeconds = now.getUTCSeconds();
      
      // Window is open: Saturday (6) from 12:00 to Sunday (0) 12:00 UTC
      const windowOpen = (utcDay === 6 && utcHour >= 12) || (utcDay === 0 && utcHour < 12);
      setIsOpen(windowOpen);
      
      if (windowOpen) {
        // Calculate time remaining until Sunday 12pm GMT
        let hoursLeft, minsLeft, secsLeft;
        if (utcDay === 6) {
          // Saturday after 12pm - hours until midnight + 12 hours Sunday
          hoursLeft = (23 - utcHour) + 12;
          minsLeft = 59 - utcMinutes;
          secsLeft = 59 - utcSeconds;
        } else {
          // Sunday before 12pm
          hoursLeft = 11 - utcHour;
          minsLeft = 59 - utcMinutes;
          secsLeft = 59 - utcSeconds;
        }
        setCountdown(`${hoursLeft}h ${minsLeft}m ${secsLeft}s remaining`);
      } else {
        // Calculate time until next Saturday 12pm GMT
        let daysUntil = (6 - utcDay + 7) % 7;
        if (daysUntil === 0 && utcHour >= 12) {
          daysUntil = 7;
        }
        
        // Calculate exact time until Saturday 12:00 GMT
        const nextSaturday = new Date(now);
        nextSaturday.setUTCDate(now.getUTCDate() + daysUntil);
        nextSaturday.setUTCHours(12, 0, 0, 0);
        
        const diff = nextSaturday - now;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const secs = Math.floor((diff % (1000 * 60)) / 1000);
        
        if (days > 0) {
          setCountdown(`${days}d ${hours}h ${mins}m ${secs}s`);
        } else {
          setCountdown(`${hours}h ${mins}m ${secs}s`);
        }
      }
    };
    
    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);
    return () => clearInterval(interval);
  }, [stats]);
  
  if (!stats) return null;
  
  return (
    <div className={`${isOpen 
      ? 'bg-gradient-to-r from-green-500/20 via-green-500/10 to-green-500/20 border-green-500' 
      : 'bg-gradient-to-r from-[#FF0099]/10 via-[#0A0A0A] to-[#00F0FF]/10 border-[#262626]'
    } border p-2 sm:p-3 text-center`} data-testid="transfer-window-banner">
      <div className="flex items-center justify-center gap-2 sm:gap-3 flex-wrap">
        <Clock className={`w-4 h-4 sm:w-5 sm:h-5 ${isOpen ? 'text-green-400 animate-pulse' : 'text-[#00F0FF]'}`} />
        <span className="text-[#A1A1AA] font-medium text-xs sm:text-sm">Transfer Window:</span>
        {isOpen ? (
          <span className="text-green-400 font-bold animate-pulse text-xs sm:text-sm">
            🟢 OPEN - {countdown}
          </span>
        ) : (
          <span className="text-[#00F0FF] font-bold text-xs sm:text-sm">
            Opens in {countdown}
          </span>
        )}
      </div>
      <p className="text-[10px] sm:text-xs text-[#A1A1AA]/70 mt-1">
        {isOpen 
          ? "Make up to 3 transfers now! Window closes Sunday 12pm GMT" 
          : "3 transfers allowed per window • Every Saturday 12pm - Sunday 12pm GMT"
        }
      </p>
    </div>
  );
};

export default TransferWindowBanner;
