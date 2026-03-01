import { useState, useEffect, useCallback } from "react";
import { Eye, Plus, Trash2, TrendingDown, TrendingUp, AlertCircle, X } from "lucide-react";
import { getPriceWatches, createPriceWatch, deletePriceWatch, fetchAutocomplete } from "../../api";
import TierBadge from "../common/TierBadge";

const PriceWatch = ({ teamId, onClose }) => {
  const [watches, setWatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [selectedCeleb, setSelectedCeleb] = useState(null);
  const [targetPrice, setTargetPrice] = useState("");
  const [alertType, setAlertType] = useState("below");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const loadWatches = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getPriceWatches(teamId);
      setWatches(data);
    } catch (e) {
      console.error("Failed to load watches:", e);
    } finally {
      setLoading(false);
    }
  }, [teamId]);

  useEffect(() => {
    loadWatches();
  }, [loadWatches]);

  const handleSearch = async (query) => {
    setSearchQuery(query);
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const results = await fetchAutocomplete(query);
      setSuggestions(results.slice(0, 5));
    } catch (e) {
      console.error("Search error:", e);
    }
  };

  const selectCelebrity = (celeb) => {
    setSelectedCeleb(celeb);
    setSearchQuery(celeb.name);
    setSuggestions([]);
    setTargetPrice(Math.floor(celeb.price * 0.8).toString()); // Default to 20% below current
  };

  const handleCreateWatch = async () => {
    if (!selectedCeleb || !targetPrice) {
      setError("Please select a celebrity and set a target price");
      return;
    }
    
    const price = parseFloat(targetPrice);
    if (isNaN(price) || price <= 0) {
      setError("Please enter a valid target price");
      return;
    }

    try {
      setCreating(true);
      setError("");
      await createPriceWatch(teamId, selectedCeleb.name, price, alertType);
      await loadWatches();
      setShowAddForm(false);
      setSelectedCeleb(null);
      setSearchQuery("");
      setTargetPrice("");
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to create price watch");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (watchId) => {
    try {
      await deletePriceWatch(teamId, watchId);
      setWatches(watches.filter(w => w.id !== watchId));
    } catch (e) {
      console.error("Failed to delete watch:", e);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4" data-testid="price-watch-modal">
      {/* ... rest of your component remains unchanged ... */}
    </div>
  );
};

export default PriceWatch;