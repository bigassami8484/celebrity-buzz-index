import { useState, useRef, useEffect } from "react";
import { Search, TrendingUp } from "lucide-react";
import { fetchAutocomplete } from "../../api";
import TierBadge from "../common/TierBadge";

const SearchBar = ({ onSearch, loading }) => {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const searchRef = useRef(null);
  const debounceRef = useRef(null);
  
  // Fetch autocomplete suggestions
  const fetchSuggestions = async (searchQuery) => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    
    setLoadingSuggestions(true);
    try {
      const results = await fetchAutocomplete(searchQuery);
      setSuggestions(results);
    } catch (e) {
      console.error("Autocomplete error:", e);
      setSuggestions([]);
    } finally {
      setLoadingSuggestions(false);
    }
  };
  
  // Debounced search
  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    setShowSuggestions(true);
    
    // Clear previous timeout
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    
    // Set new timeout for debounced search
    debounceRef.current = setTimeout(() => {
      fetchSuggestions(value);
    }, 300);
  };
  
  const handleSelectSuggestion = (suggestion) => {
    onSearch(suggestion.name);
    setQuery("");
    setSuggestions([]);
    setShowSuggestions(false);
  };
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setQuery("");
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };
  
  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  
  return (
    <div ref={searchRef} className="search-container mb-2 px-4 relative">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => setShowSuggestions(true)}
          placeholder="Search any celebrity worldwide..."
          className="search-input"
          data-testid="search-input"
        />
        <button type="submit" className="search-button" disabled={loading} data-testid="search-button">
          <Search className="w-5 h-5" />
        </button>
      </form>
      
      {/* Helper text - directly under search bar */}
      <p className="text-center text-base text-[#FFD700] mt-3 mb-2 font-medium" data-testid="search-helper-text">
        Select a category or search for any celebrity
      </p>
      
      {/* Autocomplete Suggestions */}
      {showSuggestions && (suggestions.length > 0 || loadingSuggestions) && (
        <div className="absolute left-4 right-4 top-[55px] bg-[#0A0A0A] border border-[#262626] max-h-96 overflow-y-auto z-50" data-testid="autocomplete-dropdown">
          {loadingSuggestions ? (
            <div className="p-4 text-center text-[#A1A1AA]">Searching Wikipedia...</div>
          ) : (
            suggestions.map((suggestion, idx) => (
              <div
                key={idx}
                onClick={() => handleSelectSuggestion(suggestion)}
                className="flex items-center gap-3 p-3 hover:bg-[#1A1A1A] cursor-pointer border-b border-[#262626] last:border-b-0"
                data-testid={`suggestion-${idx}`}
              >
                <img
                  src={suggestion.image}
                  alt={suggestion.name}
                  className="w-12 h-12 rounded object-cover"
                  onError={(e) => {
                    e.target.src = `https://ui-avatars.com/api/?name=${suggestion.name}&size=48&background=FF0099&color=fff`;
                  }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white truncate">{suggestion.name}</span>
                    <TierBadge tier={suggestion.tier || suggestion.estimated_tier} />
                  </div>
                  <p className="text-xs text-[#A1A1AA] truncate">{suggestion.description}</p>
                </div>
                <div className="text-right">
                  <div className="text-[#FFD700] font-bold">£{suggestion.price || suggestion.estimated_price}M</div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
