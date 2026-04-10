import "./Navbar.css";

const navLinks = [
  { label: "Explorar", href: "#explore" },
  { label: "Estancias", href: "#stays" },
  { label: "Mis viajes", href: "#my-trips" },
];

function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar__inner">
        <a className="navbar__logo" href="/">
          TravelHub
        </a>

        <nav className="navbar__menu" aria-label="Principal">
          <ul className="navbar__menu-list">
            {navLinks.map(({ label, href }) => (
              <li key={label}>
                <a className="navbar__link" href={href}>
                  {label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <form className="navbar__search" role="search" onSubmit={(e) => e.preventDefault()}>
          <label htmlFor="nav-search" className="visually-hidden">
            Buscar destinos
          </label>
          <input
            id="nav-search"
            type="search"
            name="q"
            placeholder="Buscar destinos..."
            className="navbar__search-input"
            autoComplete="off"
          />
        </form>

        <div className="navbar__actions">
          <a className="navbar__btn navbar__btn--ghost" href="/login">
            Iniciar sesión
          </a>
          <a className="navbar__btn navbar__btn--primary" href="/signup">
            Registrarse
          </a>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
