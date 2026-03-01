import { tierColors } from "../../api";

const TierBadge = ({ tier }) => {
  const tierStyle = tierColors[tier] || tierColors.D;
  return (
    <span className={`${tierStyle.bg} ${tierStyle.text} px-2 py-1 text-[10px] font-bold uppercase tracking-wider`}>
      {tierStyle.label}
    </span>
  );
};

export default TierBadge;
