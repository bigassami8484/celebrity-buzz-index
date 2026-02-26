/**
 * Custom hooks for league management.
 * Extracts league-related state and logic from App.js
 */
import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import {
  fetchTeamLeagues,
  createLeagueAPI,
  joinLeagueAPI,
  fetchLeagueLeaderboard,
} from '../api';

export function useLeagues() {
  const [leagues, setLeagues] = useState([]);
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [leagueLeaderboard, setLeagueLeaderboard] = useState([]);

  // Fetch team leagues
  const fetchLeagues = useCallback(async (teamId) => {
    if (!teamId) return [];
    try {
      const leaguesData = await fetchTeamLeagues(teamId);
      setLeagues(leaguesData);
      return leaguesData;
    } catch (e) {
      console.error("Error fetching leagues:", e);
      return [];
    }
  }, []);

  // Create a new league
  const createLeague = useCallback(async (name, teamId) => {
    if (!teamId) return null;
    try {
      const newLeague = await createLeagueAPI(name, teamId);
      setLeagues(prev => [...prev, newLeague]);
      toast.success(`League "${name}" created! Share code: ${newLeague.code}`);
      return newLeague;
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to create league");
      return null;
    }
  }, []);

  // Join a league
  const joinLeague = useCallback(async (code, teamId) => {
    if (!teamId) return null;
    try {
      const result = await joinLeagueAPI(code, teamId);
      setLeagues(prev => [...prev, result.league]);
      toast.success(result.message);
      return result.league;
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to join league");
      return null;
    }
  }, []);

  // View league details
  const viewLeague = useCallback(async (league) => {
    try {
      const lb = await fetchLeagueLeaderboard(league.id);
      setLeagueLeaderboard(lb);
      setSelectedLeague(league);
      return lb;
    } catch (e) {
      toast.error("Failed to load league");
      return null;
    }
  }, []);

  // Close league detail
  const closeLeagueDetail = useCallback(() => {
    setSelectedLeague(null);
    setLeagueLeaderboard([]);
  }, []);

  return {
    leagues,
    setLeagues,
    selectedLeague,
    setSelectedLeague,
    leagueLeaderboard,
    fetchLeagues,
    createLeague,
    joinLeague,
    viewLeague,
    closeLeagueDetail,
  };
}
