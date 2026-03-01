import { useState } from "react";
import { X } from "lucide-react";

const TeamCustomizeModal = ({ team, options, onSave, onClose }) => {
  const [teamName, setTeamName] = useState(team?.team_name || "");
  const [selectedColor, setSelectedColor] = useState(team?.team_color || "pink");
  const [selectedIcon, setSelectedIcon] = useState(team?.team_icon || "star");
  const [nameError, setNameError] = useState("");
  
  // Simple client-side profanity check (basic words only - server has full list)
  const checkName = (name) => {
    const badWords = ["fuck", "shit", "cunt", "bitch", "ass", "dick", "cock", "wanker", "twat", "nigger", "nigga", "faggot", "retard"];
    const nameLower = name.toLowerCase().replace(/[^a-z0-9]/g, '');
    for (const word of badWords) {
      if (nameLower.includes(word)) {
        return "Team name contains inappropriate language";
      }
    }
    return "";
  };
  
  const handleNameChange = (e) => {
    const newName = e.target.value;
    setTeamName(newName);
    setNameError(checkName(newName));
  };
  
  const handleSave = () => {
    const error = checkName(teamName);
    if (error) {
      setNameError(error);
      return;
    }
    onSave(teamName, selectedColor, selectedIcon);
  };
  
  const selectedColorHex = options.colors?.find(c => c.id === selectedColor)?.hex || "#FF0099";
  const selectedIconEmoji = options.icons?.find(i => i.id === selectedIcon)?.emoji || "⭐";
  
  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-[#0A0A0A] border border-[#262626] max-w-md w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="font-anton text-2xl uppercase text-[#00F0FF]">Customize Team</h3>
            <button onClick={onClose} className="text-[#A1A1AA] hover:text-white">
              <X className="w-6 h-6" />
            </button>
          </div>
          
          {/* Preview */}
          <div className="bg-[#1A1A1A] p-4 mb-6 text-center">
            <div 
              className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-3 text-3xl"
              style={{ backgroundColor: selectedColorHex }}
            >
              {selectedIconEmoji}
            </div>
            <p className="font-bold text-lg">{teamName || "My Team"}</p>
            <p className="text-xs text-[#A1A1AA]">Preview</p>
          </div>
          
          {/* Team Name */}
          <div className="mb-6">
            <label className="block text-sm text-[#A1A1AA] mb-2">Team Name</label>
            <input
              type="text"
              value={teamName}
              onChange={handleNameChange}
              className={`w-full bg-[#1A1A1A] border p-3 text-white ${nameError ? 'border-red-500' : 'border-[#262626]'}`}
              placeholder="Enter team name..."
              maxLength={30}
              data-testid="team-name-input"
            />
            {nameError && (
              <p className="text-red-500 text-xs mt-1">{nameError}</p>
            )}
          </div>
          
          {/* Colors */}
          <div className="mb-6">
            <label className="block text-sm text-[#A1A1AA] mb-2">Team Color</label>
            <div className="grid grid-cols-4 gap-2">
              {options.colors?.map((color) => (
                <button
                  key={color.id}
                  onClick={() => setSelectedColor(color.id)}
                  className={`w-full aspect-square rounded-lg border-2 transition-all ${selectedColor === color.id ? 'border-white scale-110' : 'border-transparent'}`}
                  style={{ backgroundColor: color.hex }}
                  title={color.name}
                />
              ))}
            </div>
          </div>
          
          {/* Icons */}
          <div className="mb-6">
            <label className="block text-sm text-[#A1A1AA] mb-2">Team Icon</label>
            <div className="grid grid-cols-6 gap-2">
              {options.icons?.map((icon) => (
                <button
                  key={icon.id}
                  onClick={() => setSelectedIcon(icon.id)}
                  className={`text-2xl p-2 rounded-lg border-2 transition-all ${selectedIcon === icon.id ? 'border-[#00F0FF] bg-[#1A1A1A]' : 'border-transparent hover:bg-[#1A1A1A]'}`}
                  title={icon.name}
                >
                  {icon.emoji}
                </button>
              ))}
            </div>
          </div>
          
          {/* Save Button */}
          <button
            onClick={handleSave}
            className="w-full bg-gradient-to-r from-[#FF0099] to-[#00F0FF] text-white font-bold py-3 uppercase"
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  );
};

export default TeamCustomizeModal;
