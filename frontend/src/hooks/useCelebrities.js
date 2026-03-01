/**
 * Custom hooks for celebrity data fetching.
 * Extracts celebrity-related data fetching from App.js
 */
import { useState, useCallback } from 'react';
import { toast } from 'sonner';
import {
  fetchCategories as fetchCategoriesAPI,
  fetchTrending as fetchTrendingAPI,
  fetchCelebritiesByCategory as fetchCelebritiesByCategoryAPI,
  searchCelebrityAPI,
  fetchTopPicked as fetchTopPickedAPI,
  fetchHotCelebs as fetchHotCelebsAPI,
  fetchBrownBreadWatch as fetchBrownBreadWatchAPI,
  fetchHotStreaks as fetchHotStreaksAPI,
} from '../api';

export function useCelebrities() {
  const [categories, setCategories] = useState([]);
  const [activeCategory, setActiveCategory] = useState(null);
  const [celebrities, setCelebrities] = useState([]);
  const [trending, setTrending] = useState([]);
  const [topPicked, setTopPicked] = useState([]);
  const [hotCelebs, setHotCelebs] = useState([]);
  const [brownBreadWatch, setBrownBreadWatch] = useState([]);
  const [hotStreaks, setHotStreaks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchedCeleb, setSearchedCeleb] = useState(null);

  // Fetch categories
  const fetchCategories = useCallback(async () => {
    try {
      const cats = await fetchCategoriesAPI();
      setCategories(cats);
      return cats;
    } catch (e) {
      console.error("Error fetching categories:", e);
      return [];
    }
  }, []);

  // Fetch trending
  const fetchTrending = useCallback(async () => {
    try {
      const trendingData = await fetchTrendingAPI();
      setTrending(trendingData);
      return trendingData;
    } catch (e) {
      console.error("Error fetching trending:", e);
      return [];
    }
  }, []);

  // Fetch celebrities by category
  const fetchCelebritiesByCategory = useCallback(async (category) => {
    setLoading(true);
    try {
      const celebs = await fetchCelebritiesByCategoryAPI(category);
      setCelebrities(celebs);
      return celebs;
    } catch (e) {
      console.error("Error fetching celebrities:", e);
      toast.error("Failed to load celebrities");
      return [];
    } finally {
      setLoading(false);
    }
  }, []);

  // Search celebrity
  const searchCelebrity = useCallback(async (name) => {
    setSearchLoading(true);
    try {
      const celeb = await searchCelebrityAPI(name);
      if (celeb) {
        setSearchedCeleb(celeb);
        return celeb;
      }
    } catch (e) {
      console.error("Search error:", e);
      toast.error("Celebrity not found");
    } finally {
      setSearchLoading(false);
    }
    return null;
  }, []);

  // Fetch top picked
  const fetchTopPicked = useCallback(async () => {
    try {
      const picked = await fetchTopPickedAPI();
      setTopPicked(picked);
      return picked;
    } catch (e) {
      console.error("Error fetching top picked:", e);
      return [];
    }
  }, []);

  // Fetch hot celebs
  const fetchHotCelebs = useCallback(async () => {
    try {
      const celebs = await fetchHotCelebsAPI();
      setHotCelebs(celebs || []);
      return celebs;
    } catch (e) {
      console.error("Error fetching hot celebs:", e);
      setHotCelebs([]);
      return [];
    }
  }, []);

  // Fetch brown bread watch
  const fetchBrownBreadWatch = useCallback(async () => {
    try {
      const watchList = await fetchBrownBreadWatchAPI();
      setBrownBreadWatch(watchList);
      return watchList;
    } catch (e) {
      console.error("Error fetching brown bread watch:", e);
      return [];
    }
  }, []);

  // Fetch hot streaks
  const fetchHotStreaks = useCallback(async () => {
    try {
      const streaks = await fetchHotStreaksAPI();
      setHotStreaks(streaks);
      return streaks;
    } catch (e) {
      console.error("Error fetching hot streaks:", e);
      return [];
    }
  }, []);

  // Category change handler
  const handleCategoryChange = useCallback((category) => {
    if (category) {
      setCelebrities([]);
      setActiveCategory(category);
      setTimeout(() => {
        fetchCelebritiesByCategory(category);
      }, 50);
    } else {
      setActiveCategory(null);
      setCelebrities([]);
    }
  }, [fetchCelebritiesByCategory]);

  return {
    categories,
    activeCategory,
    setActiveCategory,
    celebrities,
    setCelebrities,
    trending,
    topPicked,
    hotCelebs,
    brownBreadWatch,
    hotStreaks,
    loading,
    searchLoading,
    searchedCeleb,
    setSearchedCeleb,
    fetchCategories,
    fetchTrending,
    fetchCelebritiesByCategory,
    searchCelebrity,
    fetchTopPicked,
    fetchHotCelebs,
    fetchBrownBreadWatch,
    fetchHotStreaks,
    handleCategoryChange,
  };
}
