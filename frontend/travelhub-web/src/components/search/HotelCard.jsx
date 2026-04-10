import { IconStar } from "../home/HeroIcons";
import "./HotelCard.css";

function HotelCard({ hotel, copy }) {
  const ratingDisplay =
    typeof hotel.rating === "number" ? hotel.rating.toFixed(2) : String(hotel.rating);
  const maxAmenities = 4;
  const visibleAmenities = hotel.amenities.slice(0, maxAmenities);
  const restCount = Math.max(0, hotel.amenities.length - maxAmenities);

  return (
    <article className="hotel-card">
      <div className="hotel-card__media">
        <img
          className="hotel-card__image"
          src={hotel.image}
          alt={copy.imageAlt(hotel.name)}
          loading="lazy"
          width="320"
          height="200"
        />
      </div>

      <div className="hotel-card__body">
        <div className="hotel-card__head">
          <h3 className="hotel-card__title">{hotel.name}</h3>
          <p className="hotel-card__location">{hotel.location}</p>
        </div>

        <div
          className="hotel-card__rating"
          aria-label={copy.ratingAria(ratingDisplay)}
        >
          <IconStar className="hotel-card__star" />
          <span className="hotel-card__rating-value">{ratingDisplay}</span>
          <span className="hotel-card__reviews">
            ({copy.reviews(hotel.reviewsCount)})
          </span>
        </div>

        {visibleAmenities.length > 0 && (
          <ul className="hotel-card__amenities">
            {visibleAmenities.map((item) => (
              <li key={item} className="hotel-card__amenity">
                {item}
              </li>
            ))}
            {restCount > 0 && (
              <li className="hotel-card__amenity hotel-card__amenity--more">
                {copy.amenitiesMore(restCount)}
              </li>
            )}
          </ul>
        )}

        <p
          className={`hotel-card__refund${hotel.isRefundable ? " hotel-card__refund--yes" : " hotel-card__refund--no"}`}
        >
          {hotel.isRefundable ? copy.refundable : copy.notRefundable}
        </p>
      </div>

      <div className="hotel-card__aside">
        <div className="hotel-card__price-block">
          <span className="hotel-card__price-amount">
            {copy.priceLabel(hotel.price)}
          </span>
          <span className="hotel-card__price-meta">
            {copy.perNight}
            <span className="hotel-card__price-sep"> · </span>
            {copy.priceTaxNote}
          </span>
        </div>
        <button type="button" className="hotel-card__book">
          {copy.bookNow}
        </button>
      </div>
    </article>
  );
}

export default HotelCard;
