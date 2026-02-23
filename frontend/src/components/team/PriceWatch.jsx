import { useState, useEffect } from "react";
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

  useEffect(() => {
    loadWatches();
  }, [teamId]);

  const loadWatches = async () => {
    try {
      setLoading(true);
      const data = await getPriceWatches(teamId);
      setWatches(data);
    } catch (e) {
      console.error("Failed to load watches:", e);
    } finally {
      setLoading(false);
    }
  };

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
      <div className="bg-[#0A0A0A] border border-[#262626] rounded-lg w-full max-w-md max-h-[80vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#262626]">
          <div className="flex items-center gap-2">
            <Eye className="w-5 h-5 text-[#FF0099]" />
            <h2 className="text-lg font-bold text-white">Price Watch</h2>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white" data-testid="close-price-watch">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="text-center py-8 text-gray-400">Loading watches...</div>
          ) : (
            <>
              {/* Add New Watch */}
              {!showAddForm ? (
                <button
                  onClick={() => setShowAddForm(true)}
                  className="w-full flex items-center justify-center gap-2 p-3 bg-[#FF0099]/10 border border-[#FF0099]/30 rounded-lg text-[#FF0099] hover:bg-[#FF0099]/20 transition-colors mb-4"
                  data-testid="add-price-watch-btn"
                >
                  <Plus className="w-4 h-4" />
                  Add Price Watch
                </button>
              ) : (
                <div className="bg-[#1A1A1A] rounded-lg p-4 mb-4" data-testid="add-watch-form">
                  <h3 className="text-sm font-medium text-white mb-3">Watch a Celebrity</h3>
                  
                  {/* Search */}
                  <div className="relative mb-3">
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => handleSearch(e.target.value)}
                      placeholder="Search celebrity..."
                      className="w-full p-2 bg-[#0A0A0A] border border-[#333] rounded text-white text-sm"
                      data-testid="watch-search-input"
                    />
                    {suggestions.length > 0 && (
                      <div className="absolute left-0 right-0 top-full mt-1 bg-[#0A0A0A] border border-[#333] rounded-lg max-h-40 overflow-y-auto z-10">
                        {suggestions.map((s, idx) => (
                          <div
                            key={idx}
                            onClick={() => selectCelebrity(s)}
                            className="flex items-center gap-2 p-2 hover:bg-[#1A1A1A] cursor-pointer"
                          >
                            <img
                              src={s.image}
                              alt={s.name}
                              className="w-8 h-8 rounded object-cover"
                              onError={(e) => {
                                e.target.src = `https://ui-avatars.com/api/?name=${s.name}&size=32&background=FF0099&color=fff`;
                              }}
                            />
                            <div className="flex-1">
                              <span className="text-white text-sm">{s.name}</span>
                            </div>
                            <span className="text-[#FFD700] text-sm">£{s.price}M</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {selectedCeleb && (
                    <div className="bg-[#0A0A0A] rounded p-2 mb-3 flex items-center gap-2">
                      <img
                        src={selectedCeleb.image}
                        alt={selectedCeleb.name}
                        className="w-10 h-10 rounded object-cover"
                        onError={(e) => {
                          e.target.src = `https://ui-avatars.com/api/?name=${selectedCeleb.name}&size=40&background=FF0099&color=fff`;
                        }}
                      />
                      <div className="flex-1">
                        <div className="text-white text-sm font-medium">{selectedCeleb.name}</div>
                        <div className="text-gray-400 text-xs">Current: £{selectedCeleb.price}M</div>
                      </div>
                      <TierBadge tier={selectedCeleb.tier} />
                    </div>
                  )}

                  {/* Alert Type */}
                  <div className="flex gap-2 mb-3">
                    <button
                      onClick={() => setAlertType("below")}
                      className={`flex-1 p-2 rounded text-sm flex items-center justify-center gap-1 ${
                        alertType === "below" 
                          ? "bg-green-500/20 border border-green-500 text-green-400" 
                          : "bg-[#0A0A0A] border border-[#333] text-gray-400"
                      }`}
                      data-testid="alert-type-below"
                    >
                      <TrendingDown className="w-4 h-4" />
                      Price Drops
                    </button>
                    <button
                      onClick={() => setAlertType("above")}
                      className={`flex-1 p-2 rounded text-sm flex items-center justify-center gap-1 ${
                        alertType === "above" 
                          ? "bg-red-500/20 border border-red-500 text-red-400" 
                          : "bg-[#0A0A0A] border border-[#333] text-gray-400"
                      }`}
                      data-testid="alert-type-above"
                    >
                      <TrendingUp className="w-4 h-4" />
                      Price Rises
                    </button>
                  </div>

                  {/* Target Price */}
                  <div className="mb-3">
                    <label className="text-xs text-gray-400 mb-1 block">
                      Target Price (£M)
                    </label>
                    <input
                      type="number"
                      value={targetPrice}
                      onChange={(e) => setTargetPrice(e.target.value)}
                      placeholder="e.g. 8.0"
                      step="0.5"
                      min="0.5"
                      max="15"
                      className="w-full p-2 bg-[#0A0A0A] border border-[#333] rounded text-white text-sm"
                      data-testid="target-price-input"
                    />
                  </div>

                  {error && (
                    <div className="text-red-400 text-xs mb-3 flex items-center gap-1">
                      <AlertCircle className="w-3 h-3" />
                      {error}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setShowAddForm(false);
                        setSelectedCeleb(null);
                        setSearchQuery("");
                        setError("");
                      }}
                      className="flex-1 p-2 bg-[#333] rounded text-gray-300 text-sm"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleCreateWatch}
                      disabled={!selectedCeleb || creating}
                      className="flex-1 p-2 bg-[#FF0099] rounded text-white text-sm disabled:opacity-50"
                      data-testid="create-watch-btn"
                    >
                      {creating ? "Creating..." : "Watch Price"}
                    </button>
                  </div>
                </div>
              )}

              {/* Watches List */}
              {watches.length === 0 ? (
                <div className="text-center py-8">
                  <Eye className="w-10 h-10 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400 text-sm">No price watches yet</p>
                  <p className="text-gray-500 text-xs">Track celebrities and get notified when their price hits your target</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {watches.map((watch) => (
                    <div
                      key={watch.id}
                      className={`flex items-center gap-3 p-3 rounded-lg border ${
                        watch.target_reached 
                          ? "bg-green-500/10 border-green-500/50" 
                          : "bg-[#1A1A1A] border-[#333]"
                      }`}
                      data-testid={`watch-item-${watch.id}`}
                    >
                      <img
                        src={watch.image}
                        alt={watch.celebrity_name}
                        className="w-12 h-12 rounded object-cover"
                        onError={(e) => {
                          e.target.src = `https://ui-avatars.com/api/?name=${watch.celebrity_name}&size=48&background=FF0099&color=fff`;
                        }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium text-sm truncate">{watch.celebrity_name}</span>
                          <TierBadge tier={watch.tier} />
                        </div>
                        <div className="flex items-center gap-2 text-xs mt-1">
                          <span className="text-gray-400">Now: £{watch.current_price}M</span>
                          <span className="text-gray-600">→</span>
                          <span className={watch.target_reached ? "text-green-400" : "text-[#FFD700]"}>
                            Target: £{watch.target_price}M
                          </span>
                          {watch.alert_type === "below" ? (
                            <TrendingDown className="w-3 h-3 text-green-400" />
                          ) : (
                            <TrendingUp className="w-3 h-3 text-red-400" />
                          )}
                        </div>
                        {watch.target_reached && (
                          <div className="text-green-400 text-xs mt-1 flex items-center gap-1">
                            <AlertCircle className="w-3 h-3" />
                            Target reached! Time to buy!
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => handleDelete(watch.id)}
                        className="text-gray-500 hover:text-red-400 p-2"
                        data-testid={`delete-watch-${watch.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Info */}
              <div className="mt-4 p-3 bg-[#1A1A1A] rounded-lg">
                <p className="text-xs text-gray-400">
                  <strong className="text-[#FF0099]">Pro tip:</strong> Watch celebrities before the transfer window opens. When their price drops to your target, add them to your team!
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default PriceWatch;
