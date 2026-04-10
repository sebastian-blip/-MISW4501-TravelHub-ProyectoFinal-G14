import { useState } from "react";
import "./ExploreSection.css";

const CATEGORIES = ["Vuelos", "Hoteles", "Estancias", "Villas", "Resorts"];

function ExploreSection() {
  const [active, setActive] = useState("Estancias");

  return (
    <section className="explore-section" id="explore" aria-labelledby="explore-heading">
      <div className="explore-section__header">
        <p className="explore-section__eyebrow">Explora por tipo</p>
        <h2 id="explore-heading" className="explore-section__title">
          Explorar
        </h2>
      </div>
      <nav className="explore-section__nav" aria-label="Explorar por categoría">
        <div className="explore-section__nav-inner" role="group">
          {CATEGORIES.map((label) => {
            const isActive = active === label;
            return (
              <button
                key={label}
                type="button"
                className={`explore-chip${isActive ? " explore-chip--active" : ""}`}
                aria-pressed={isActive}
                onClick={() => setActive(label)}
              >
                {label}
              </button>
            );
          })}
        </div>
      </nav>
    </section>
  );
}

export default ExploreSection;
