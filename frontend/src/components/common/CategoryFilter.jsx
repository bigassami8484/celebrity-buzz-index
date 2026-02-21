import { Film, Tv, Music, Trophy, Crown, Star, Users } from "lucide-react";

const categoryIcons = {
  movie_stars: Film,
  tv_actors: Tv,
  musicians: Music,
  athletes: Trophy,
  royals: Crown,
  reality_tv: Star,
  other: Users,
};

const CategoryFilter = ({ categories, activeCategory, onSelect }) => (
  <div className="flex flex-wrap gap-3 justify-center py-6 px-4 mb-6" data-testid="category-filter">
    <button
      className={`category-pill ${!activeCategory ? 'active' : ''}`}
      onClick={() => onSelect(null)}
      data-testid="category-all"
    >
      All
    </button>
    {categories.map((cat) => {
      const Icon = categoryIcons[cat.id] || Star;
      return (
        <button
          key={cat.id}
          className={`category-pill flex items-center gap-2 ${activeCategory === cat.id ? 'active' : ''}`}
          onClick={() => onSelect(cat.id)}
          data-testid={`category-${cat.id}`}
        >
          <Icon className="w-4 h-4" />
          {cat.name}
        </button>
      );
    })}
  </div>
);

export default CategoryFilter;
