import { useState } from "react";
import { IconCalendar, IconMapPin, IconSearch, IconUsers } from "./HeroIcons";
import "./Hero.css";

const guestOptions = [
  { value: "1", label: "1 huésped" },
  { value: "2", label: "2 huéspedes" },
  { value: "3", label: "3 huéspedes" },
  { value: "4", label: "4 huéspedes" },
  { value: "5", label: "5+ huéspedes" },
];

function Hero() {
  const [destination, setDestination] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [guests, setGuests] = useState("2");

  const handleCheckInChange = (e) => {
    const value = e.target.value;
    setCheckIn(value);
    if (checkOut && value && checkOut < value) {
      setCheckOut("");
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log({ destination, checkIn, checkOut, guests });
  };

  return (
    <section className="home-hero" aria-labelledby="home-hero-title">
      <div className="home-hero__content">
        <div className="home-hero__intro">
          <h1 id="home-hero-title" className="home-hero__title">
            Encuentra tu estadía perfecta
          </h1>
          <p className="home-hero__subtitle">
            Descubre hoteles, villas y alojamientos entre más de 50.000 anuncios en todo el mundo
          </p>
        </div>

        <form className="home-hero__form" onSubmit={handleSubmit} role="search">
          <div className="home-hero__search-card">
            <div className="home-hero__search-row">
              <div className="home-hero__field home-hero__field--destination">
                <label htmlFor="hero-destination" className="home-hero__field-label">
                  Destino
                </label>
                <div className="home-hero__field-control">
                  <IconMapPin className="home-hero__field-icon" aria-hidden="true" />
                  <input
                    id="hero-destination"
                    type="text"
                    name="destination"
                    placeholder="¿A dónde vas?"
                    className="home-hero__field-input"
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    autoComplete="off"
                  />
                </div>
              </div>

              <div className="home-hero__field home-hero__field--datecol">
                <label htmlFor="hero-checkin" className="home-hero__field-label">
                  Fecha de entrada
                </label>
                <div className="home-hero__field-control">
                  <IconCalendar className="home-hero__field-icon" aria-hidden="true" />
                  <input
                    id="hero-checkin"
                    type="date"
                    name="checkIn"
                    className="home-hero__field-input home-hero__field-input--date"
                    value={checkIn}
                    onChange={handleCheckInChange}
                  />
                </div>
              </div>

              <div className="home-hero__field home-hero__field--datecol">
                <label htmlFor="hero-checkout" className="home-hero__field-label">
                  Fecha de salida
                </label>
                <div className="home-hero__field-control">
                  <IconCalendar className="home-hero__field-icon" aria-hidden="true" />
                  <input
                    id="hero-checkout"
                    type="date"
                    name="checkOut"
                    className="home-hero__field-input home-hero__field-input--date"
                    value={checkOut}
                    min={checkIn || undefined}
                    onChange={(e) => setCheckOut(e.target.value)}
                  />
                </div>
              </div>

              <div className="home-hero__field home-hero__field--guests">
                <label htmlFor="hero-guests" className="home-hero__field-label">
                  Huéspedes
                </label>
                <div className="home-hero__field-control">
                  <IconUsers className="home-hero__field-icon" aria-hidden="true" />
                  <select
                    id="hero-guests"
                    name="guests"
                    className="home-hero__field-select"
                    value={guests}
                    onChange={(e) => setGuests(e.target.value)}
                  >
                    {guestOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="home-hero__search-action">
                <span className="home-hero__field-label home-hero__field-label--spacer" aria-hidden="true">
                  Buscar
                </span>
                <button type="submit" className="home-hero__search-btn" aria-label="Buscar">
                  <IconSearch />
                </button>
              </div>
            </div>
          </div>

          <p className="home-hero__trust">
            <span className="home-hero__trust-item">✓ Más de 50.000 propiedades</span>
            <span className="home-hero__trust-sep" aria-hidden="true">
              ·
            </span>
            <span className="home-hero__trust-item">✓ Mejor precio garantizado</span>
            <span className="home-hero__trust-sep" aria-hidden="true">
              ·
            </span>
            <span className="home-hero__trust-item">✓ Cancelación gratuita</span>
            <span className="home-hero__trust-sep" aria-hidden="true">
              ·
            </span>
            <span className="home-hero__trust-item">✓ Atención 24/7</span>
          </p>
        </form>
      </div>
    </section>
  );
}

export default Hero;
