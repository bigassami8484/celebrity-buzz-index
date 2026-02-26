/**
 * Custom hooks for team management.
 * Extracts team-related state and logic from App.js
 */
import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import { 
  createTeam, 
  getTeam, 
  addToTeamAPI, 
  removeFromTeamAPI, 
  customizeTeamAPI,
  feelingLucky 
} from '../api';

export function useTeam() {
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(false);

  // Initialize or fetch team
  const initTeam = useCallback(async () => {
    const storedTeamId = localStorage.getItem("teamId");
    if (storedTeamId) {
      try {
        const existingTeam = await getTeam(storedTeamId);
        setTeam(prev => prev || existingTeam);
        return existingTeam;
      } catch (e) {
        localStorage.removeItem("teamId");
      }
    }
    
    // Create new team if none exists
    try {
      const newTeam = await createTeam("My Buzz Team");
      localStorage.setItem("teamId", newTeam.id);
      setTeam(prev => prev || newTeam);
      return newTeam;
    } catch (e) {
      console.error("Error creating team:", e);
      return null;
    }
  }, []);

  // Add celebrity to team
  const addToTeam = useCallback(async (celebrity, onSuccess) => {
    if (!team) return;
    
    try {
      const result = await addToTeamAPI(team.id, celebrity.id);
      setTeam(result.team);
      
      if (result.brown_bread_bonus) {
        toast.success(`Added ${celebrity.name} + 💀 Brown Bread Bonus!`, { duration: 5000 });
      } else {
        toast.success(`Added ${celebrity.name} to your team!`);
      }
      
      if (onSuccess) onSuccess();
      return result.team;
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to add celebrity");
      return null;
    }
  }, [team]);

  // Remove celebrity from team
  const removeFromTeam = useCallback(async (celebrityId, isTransferWindowOpen) => {
    if (!team) return;
    
    // Check if team is locked
    if (team.is_locked && !isTransferWindowOpen) {
      toast.error("Team is locked! Wait for transfer window (Sunday 12pm)");
      return;
    }
    
    try {
      const updatedTeam = await removeFromTeamAPI(team.id, celebrityId);
      setTeam(updatedTeam);
      toast.success("Removed from team");
      return updatedTeam;
    } catch (e) {
      toast.error("Failed to remove celebrity");
      return null;
    }
  }, [team]);

  // Customize team
  const customizeTeam = useCallback(async (teamName, teamColor, teamIcon) => {
    if (!team) return;
    
    try {
      const updatedTeam = await customizeTeamAPI(team.id, teamName, teamColor, teamIcon);
      setTeam(updatedTeam);
      toast.success("Team customized! 🎨");
      return updatedTeam;
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to customize team");
      return null;
    }
  }, [team]);

  // Feeling lucky - add random celebrity
  const handleFeelingLucky = useCallback(async (onSuccess) => {
    if (!team) {
      toast.error("Create a team first!");
      return null;
    }
    
    if (team.celebrities?.length >= 10) {
      toast.error("Team is full! Remove a celebrity first.");
      return null;
    }
    
    setLoading(true);
    try {
      const { celebrity } = await feelingLucky(team.id);
      
      if (celebrity) {
        const result = await addToTeamAPI(team.id, celebrity.id);
        setTeam(result.team);
        
        if (result.brown_bread_bonus) {
          toast.success(`🎲 Lucky pick: ${celebrity.name} + 💀 Brown Bread Bonus!`, { duration: 5000 });
        } else {
          toast.success(`🎲 Lucky pick: ${celebrity.name} added for £${celebrity.price}M!`);
        }
        
        if (onSuccess) onSuccess();
        return result.team;
      }
    } catch (e) {
      toast.error(e.response?.data?.detail || "No luck this time! Try again.");
    } finally {
      setLoading(false);
    }
    return null;
  }, [team]);

  // Check if celebrity is in team
  const isInTeam = useCallback((celebrityId) => {
    return team?.celebrities?.some(c => c.celebrity_id === celebrityId) || false;
  }, [team]);

  // Check if can afford celebrity
  const canAfford = useCallback((price) => {
    return (team?.budget_remaining || 0) >= price;
  }, [team]);

  return {
    team,
    setTeam,
    loading,
    initTeam,
    addToTeam,
    removeFromTeam,
    customizeTeam,
    handleFeelingLucky,
    isInTeam,
    canAfford,
  };
}
