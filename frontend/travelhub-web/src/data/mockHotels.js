/**
 * Datos de ejemplo para listados de hoteles (Santorini / islas griegas).
 * Ajusta valores si tu diseño de referencia usa otros nombres o cifras.
 */
export const mockHotels = [
  {
    id: "hotel-mystique",
    name: "Mystique",
    location: "Oia, Santorini, Grecia",
    rating: 4.9,
    reviewsCount: 1284,
    price: 489,
    image:
      "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&q=80",
    amenities: [
      "Wi‑Fi",
      "Piscina infinita",
      "Spa",
      "Desayuno",
      "Traslado aeropuerto",
    ],
    isRefundable: true,
  },
  {
    id: "hotel-vedema",
    name: "Vedema",
    location: "Megalochori, Santorini, Grecia",
    rating: 4.8,
    reviewsCount: 942,
    price: 356,
    image:
      "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=800&q=80",
    amenities: ["Wi‑Fi", "Piscina", "Restaurante", "Gimnasio", "Estacionamiento"],
    isRefundable: true,
  },
  {
    id: "hotel-katikies",
    name: "Katikies",
    location: "Oia, Santorini, Grecia",
    rating: 4.95,
    reviewsCount: 2103,
    price: 612,
    image:
      "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=800&q=80",
    amenities: ["Wi‑Fi", "Spa", "Piscina", "Bar en azotea", "Servicio de habitaciones"],
    isRefundable: false,
  },
  {
    id: "hotel-canaves-oia",
    name: "Canaves Oia",
    location: "Oia, Santorini, Grecia",
    rating: 4.85,
    reviewsCount: 876,
    price: 540,
    image:
      "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=800&q=80",
    amenities: ["Wi‑Fi", "Piscina", "Spa", "Desayuno buffet", "Concierge"],
    isRefundable: true,
  },
  {
    id: "hotel-grace",
    name: "Grace Santorini",
    location: "Imerovigli, Santorini, Grecia",
    rating: 4.75,
    reviewsCount: 654,
    price: 425,
    image:
      "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=800&q=80",
    amenities: ["Wi‑Fi", "Piscina", "Restaurante", "Bar", "Traslado"],
    isRefundable: true,
  },
  {
    id: "hotel-andronis",
    name: "Andronis Luxury Suites",
    location: "Oia, Santorini, Grecia",
    rating: 4.82,
    reviewsCount: 1530,
    price: 398,
    image:
      "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=800&q=80",
    amenities: ["Wi‑Fi", "Spa", "Piscina", "Desayuno", "Terraza privada"],
    isRefundable: false,
  },
];

export default mockHotels;
