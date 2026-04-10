import "./DestinationCard.css";

function DestinationCard({ name, country, priceFrom, rating, background }) {
  const formattedRating = typeof rating === "number" ? rating.toFixed(1) : rating;

  return (
    <article
      className="destination-card"
      style={{ background }}
    >
      <div className="destination-card__inner">
        <h3 className="destination-card__name">{name}</h3>
        <p className="destination-card__country">{country}</p>
        <div className="destination-card__meta">
          <span className="destination-card__price">Desde {priceFrom}</span>
          <span
            className="destination-card__rating"
            aria-label={`Valoración ${formattedRating} de 5`}
          >
            <span className="destination-card__rating-value">{formattedRating}</span>
            <span className="destination-card__star" aria-hidden="true">
              ★
            </span>
          </span>
        </div>
      </div>
    </article>
  );
}

export default DestinationCard;
