/**
 * Textos parametrizables para la vista de resultados (fuera de componentes de presentación).
 */
export const searchResultsCopy = {
  pageTitle: "Resultados de búsqueda",
  toolbar: {
    filtersToolbarLabel: "Filtros rápidos",
    summaryLead: "128 properties in Santorini",
    summaryMeta: "12 Apr – 18 Apr · 2 guests",
    filterPrice: "Precio",
    filterRating: "Calificación",
    filterAmenities: "Amenidades",
    filterMap: "Mapa",
    sortLabel: "Ordenar resultados",
    sortBestMatch: "Mejor coincidencia",
    sortPriceLow: "Precio: menor a mayor",
    sortPriceHigh: "Precio: mayor a menor",
    sortRating: "Valoración de huéspedes",
  },
  sidebarTitle: "Filtros",
  sidebarPlaceholder:
    "Aquí irán los filtros (precio, estrellas, servicios…).",
  resultsRegionLabel: "Listado de alojamientos",
  hotelCard: {
    imageAlt: (hotelName) => `Vista del alojamiento ${hotelName}`,
    ratingAria: (value) => `Valoración ${value} de 5`,
    reviews: (count) =>
      `${count.toLocaleString("es")} ${count === 1 ? "opinión" : "opiniones"}`,
    priceLabel: (amount) => `$${amount.toLocaleString("es")}`,
    perNight: "por noche",
    priceTaxNote: "impuestos no incluidos",
    bookNow: "Reservar ahora",
    refundable: "Cancelación con reembolso",
    notRefundable: "Tarifa no reembolsable",
    amenitiesMore: (n) => `+${n} más`,
  },
};
