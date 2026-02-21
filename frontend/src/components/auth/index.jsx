import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { Mail, X, LogOut, Users } from "lucide-react";
import { toast } from "sonner";
import { AUTH_API } from "../../api";

// Auth Modal Component
export const AuthModal = ({ isOpen, onClose, onAuthSuccess, mode = "login" }) => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [magicLinkSent, setMagicLinkSent] = useState(false);
  
  if (!isOpen) return null;
  
  const handleMagicLink = async (e) => {
    e.preventDefault();
    if (!email) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${AUTH_API}/magic-link/send`, { email });
      setMagicLinkSent(true);
      toast.success("Magic link sent! Check your email.");
      
      // For dev mode, if token is returned, auto-verify
      if (response.data.dev_token) {
        toast.info("Dev mode: Auto-verifying...");
        const verifyResponse = await axios.post(`${AUTH_API}/magic-link/verify`, { 
          token: response.data.dev_token 
        });
        if (verifyResponse.data.success) {
          localStorage.setItem("session_token", verifyResponse.data.session_token);
          onAuthSuccess(verifyResponse.data.user);
          onClose();
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to send magic link");
    } finally {
      setLoading(false);
    }
  };
  
  const handleGoogleLogin = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    // Use Emergent Google Auth - dynamically build redirect URL from current location
    const redirectUrl = window.location.origin;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4" data-testid="auth-modal">
      <div className="bg-[#0A0A0A] border border-[#FF0099] p-6 max-w-md w-full relative">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-[#666] hover:text-white"
          data-testid="auth-modal-close"
        >
          <X className="w-5 h-5" />
        </button>
        
        <h2 className="font-anton text-2xl text-white mb-2 uppercase">
          {mode === "signup" ? "Create Account" : "Sign In"}
        </h2>
        <p className="text-[#A1A1AA] text-sm mb-6">
          {mode === "signup" 
            ? "Save your team and access it from any device"
            : "Access your Celebrity Buzz team"
          }
        </p>
        
        {!magicLinkSent ? (
          <>
            {/* Google Login Button - Primary */}
            <button
              onClick={handleGoogleLogin}
              className="w-full bg-white text-black py-3 px-4 font-medium flex items-center justify-center gap-3 hover:bg-gray-100 transition-colors mb-6"
              data-testid="google-login-btn"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </button>
            
            <div className="flex items-center gap-4 mb-6">
              <div className="flex-1 h-px bg-[#333]"></div>
              <span className="text-[#666] text-sm">or use email</span>
              <div className="flex-1 h-px bg-[#333]"></div>
            </div>
            
            {/* Magic Link Form */}
            <form onSubmit={handleMagicLink}>
              <label className="block text-sm text-[#A1A1AA] mb-2">Email Address</label>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="flex-1 bg-[#1A1A1A] border border-[#333] text-white px-4 py-3 focus:border-[#FF0099] outline-none"
                  data-testid="magic-link-email"
                  required
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-gradient-to-r from-[#FF0099] to-[#FF0099]/80 text-white px-6 py-3 font-bold disabled:opacity-50 flex items-center gap-2"
                  data-testid="send-magic-link-btn"
                >
                  <Mail className="w-4 h-4" />
                  {loading ? "..." : "Send"}
                </button>
              </div>
              <p className="text-xs text-[#666] mt-2">We'll send you a magic link to sign in - no password needed!</p>
            </form>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-[#FF0099]/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <Mail className="w-8 h-8 text-[#FF0099]" />
            </div>
            <h3 className="font-bold text-white text-lg mb-2">Check Your Email!</h3>
            <p className="text-[#A1A1AA]">We sent a magic link to <strong>{email}</strong></p>
            <p className="text-[#666] text-sm mt-4">Click the link in the email to sign in</p>
            <button
              onClick={() => setMagicLinkSent(false)}
              className="mt-6 text-[#00F0FF] hover:underline text-sm"
            >
              Use a different email
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// AuthCallback Component - Handles the OAuth redirect with session_id
export const AuthCallback = ({ onAuthSuccess, onAuthError }) => {
  const hasProcessed = useRef(false);
  
  useEffect(() => {
    // Use ref to prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;
    
    const processAuth = async () => {
      // Extract session_id from URL fragment
      const hash = window.location.hash;
      const params = new URLSearchParams(hash.replace('#', ''));
      const sessionId = params.get('session_id');
      
      if (!sessionId) {
        onAuthError?.("No session_id found");
        return;
      }
      
      try {
        // Exchange session_id for user session via backend
        const response = await axios.post(`${AUTH_API}/session`, { session_id: sessionId });
        
        if (response.data.success && response.data.user) {
          // Clear the URL fragment
          window.history.replaceState(null, '', window.location.pathname);
          onAuthSuccess(response.data.user);
        } else {
          throw new Error("Authentication failed");
        }
      } catch (error) {
        console.error("Auth callback error:", error);
        window.history.replaceState(null, '', window.location.pathname);
        onAuthError?.(error.response?.data?.detail || "Authentication failed");
      }
    };
    
    processAuth();
  }, [onAuthSuccess, onAuthError]);
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/95">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-[#FF0099] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-white font-bold">Signing you in...</p>
      </div>
    </div>
  );
};

// User Menu Component - Shows user profile and logout option
export const UserMenu = ({ user, onLogout }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!user) return null;
  
  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-2 rounded hover:bg-[#1A1A1A] transition-colors"
        data-testid="user-menu-btn"
      >
        <img 
          src={user.picture || `https://ui-avatars.com/api/?name=${user.name}&background=FF0099&color=fff`}
          alt={user.name}
          className="w-8 h-8 rounded-full object-cover border border-[#FF0099]"
        />
        <span className="text-sm text-white hidden sm:block">{user.name}</span>
      </button>
      
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 bg-[#0A0A0A] border border-[#262626] min-w-[200px] z-50">
          <div className="p-3 border-b border-[#262626]">
            <p className="text-white font-bold text-sm">{user.name}</p>
            <p className="text-[#A1A1AA] text-xs">{user.email}</p>
          </div>
          <button
            onClick={() => { setIsOpen(false); onLogout(); }}
            className="w-full flex items-center gap-2 p-3 text-left text-[#ff4444] hover:bg-[#1A1A1A] transition-colors"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm">Sign Out</span>
          </button>
        </div>
      )}
    </div>
  );
};

// Save My Team Prompt - Shows when guest user has celebrities in their team
export const SaveTeamPrompt = ({ isVisible, onSave, onDismiss, teamSize }) => {
  if (!isVisible || teamSize === 0) return null;
  
  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-slide-up" data-testid="save-team-prompt">
      <div className="bg-gradient-to-r from-[#FF0099]/20 to-[#00F0FF]/20 border border-[#FF0099] p-4 backdrop-blur-sm">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-[#FF0099] rounded-full flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5 text-white" />
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-white text-sm mb-1">Save Your Team!</h4>
            <p className="text-[#A1A1AA] text-xs mb-3">
              You have {teamSize} {teamSize === 1 ? 'celebrity' : 'celebrities'} in your team. 
              Sign in to save your progress and access it from any device!
            </p>
            <div className="flex gap-2">
              <button
                onClick={onSave}
                className="bg-[#FF0099] hover:bg-[#e6008a] text-white px-4 py-2 text-xs font-bold transition-colors"
                data-testid="save-team-btn"
              >
                Sign In to Save
              </button>
              <button
                onClick={onDismiss}
                className="text-[#666] hover:text-white px-3 py-2 text-xs transition-colors"
                data-testid="dismiss-save-prompt"
              >
                Later
              </button>
            </div>
          </div>
          <button 
            onClick={onDismiss}
            className="text-[#666] hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
