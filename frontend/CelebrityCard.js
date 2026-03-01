import { useState } from "react";

export default function CelebrityCard({ name }) {
  const [celeb, setCeleb] = useState(null);
  const [loading, setLoading] = useState(false);

  async function fetchCeleb() {
    setLoading(true);
    try {
      const res = await fetch(`/api/getCelebrity?name=${encodeURIComponent(name)}`);
      const data = await res.json();
      setCeleb(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
  <button onClick={fetchCeleb}>View {name}</button>

  {loading && <p>Loading...</p>}

  {celeb && (
    <div style={{ maxWidth: "500px" }}>

      {/* 👇 Override two misclassified celebs so they appear alive */}
      {(() => {
        if (celeb.name === "Stephen Merchant" || celeb.name === "Ricky Gervais") {
          celeb.isDead = false;
        }
      })()}

      <h2>
        {celeb.isDead ? "💀 " : ""}{celeb.name} ({celeb.tier}-list)
      </h2>
      <img
        src={celeb.image}
        alt={celeb.name}
        loading="lazy"
        style={{ width: "100%", height: "auto" }}
      />
      <p>Wikipedia Score: {celeb.wikipediaScore}</p>

      <h3>News:</h3>
      <ul>
        {celeb.news.map((article, idx) => (
          <li key={idx}>
            <a href={article.link} target="_blank" rel="noreferrer">{article.title}</a>
          </li>
        ))}
      </ul>
    </div>
  )}
</div>
