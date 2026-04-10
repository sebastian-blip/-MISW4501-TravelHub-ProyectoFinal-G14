import DestinationCard from "./DestinationCard";
import "./FeaturedDestinations.css";

const FEATURED = [
  {
    name: "Santorini",
    country: "Grecia",
    priceFrom: "$112/noche",
    rating: 4.9,
    background: "linear-gradient(145deg, #0369a1 0%, #0d9488 50%, #5eead4 100%)",
  },
  {
    name: "Kioto",
    country: "Japón",
    priceFrom: "$95/noche",
    rating: 4.8,
    background: "linear-gradient(145deg, #0e7490 0%, #06b6d4 45%, #67e8f9 100%)",
  },
  {
    name: "Marrakech",
    country: "Marruecos",
    priceFrom: "$78/noche",
    rating: 4.7,
    background: "linear-gradient(145deg, #ea580c 0%, #f97316 40%, #fbbf24 100%)",
  },
  {
    name: "Reikiavik",
    country: "Islandia",
    priceFrom: "$134/noche",
    rating: 4.8,
    background: "linear-gradient(145deg, #1d4ed8 0%, #3b82f6 42%, #818cf8 100%)",
  },
];

function FeaturedDestinations() {
  return (
    <section
      className="featured-destinations"
      aria-labelledby="featured-destinations-heading"
    >
      <div className="featured-destinations__intro">
        <p className="featured-destinations__eyebrow">Tendencias</p>
        <h2 id="featured-destinations-heading" className="featured-destinations__title">
          Destinos destacados
        </h2>
        <p className="featured-destinations__subtitle">
          Lugares seleccionados con excelente relación calidad-precio y valoraciones de huéspedes.
        </p>
      </div>
      <div className="featured-destinations__grid">
        {FEATURED.map((item) => (
          <DestinationCard
            key={item.name}
            name={item.name}
            country={item.country}
            priceFrom={item.priceFrom}
            rating={item.rating}
            background={item.background}
          />
        ))}
      </div>
    </section>
  );
}

export default FeaturedDestinations;
