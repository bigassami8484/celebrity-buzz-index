/**
 * Custom hooks for authentication.
 * Extracts auth-related state and logic from App.js
 */
import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { checkAuthStatus, logoutAPI, AUTH_API } from '../api';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [isProcessingAuth, setIsProcessingAuth] = useState(false);

  // Check existing session on mount
  const checkAuth = useCallback(async () => {
    // Don't check if we're processing OAuth callback
    if (window.location.hash?.includes('session_id=')) {
      setIsProcessingAuth(true);
      return null;
    }
    
    try {
      const res = await checkAuthStatus();
      if (res.is_authenticated && res.user) {
        setUser(res.user);
        return { user: res.user, team: res.team };
      }
    } catch (error) {
      console.log("Not authenticated");
    }
    return null;
  }, []);

  // Handle successful authentication
  const handleAuthSuccess = useCallback(async (userData, setTeam, guestTeamId) => {
    setUser(userData);
    setIsProcessingAuth(false);
    
    try {
      const res = await checkAuthStatus();
      if (res.team) {
        // User has a team linked to their account
        setTeam(res.team);
        localStorage.setItem("teamId", res.team.id);
        toast.success(`Welcome back, ${userData.name}! Your team is loaded.`);
        return res.team;
      } else if (guestTeamId) {
        // Link guest team to user's account
        try {
          const linkResult = await fetch(`${AUTH_API}/guest/convert`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ guest_team_id: guestTeamId })
          });
          if (linkResult.ok) {
            const data = await linkResult.json();
            setTeam(data.team);
            toast.success(`Welcome, ${userData.name}! Your team has been saved.`);
            return data.team;
          }
        } catch (e) {
          console.error("Failed to link guest team:", e);
        }
      }
      toast.success(`Welcome, ${userData.name}!`);
    } catch (e) {
      console.error("Error fetching user team:", e);
      toast.success(`Welcome, ${userData.name}!`);
    }
    return null;
  }, []);

  // Handle auth error
  const handleAuthError = useCallback((error) => {
    setIsProcessingAuth(false);
    toast.error(error || "Authentication failed");
  }, []);

  // Logout
  const handleLogout = useCallback(async () => {
    try {
      await logoutAPI();
      setUser(null);
      toast.success("Signed out successfully");
    } catch (error) {
      console.error("Logout error:", error);
      setUser(null);
    }
  }, []);

  return {
    user,
    setUser,
    isProcessingAuth,
    setIsProcessingAuth,
    checkAuth,
    handleAuthSuccess,
    handleAuthError,
    handleLogout,
  };
}
