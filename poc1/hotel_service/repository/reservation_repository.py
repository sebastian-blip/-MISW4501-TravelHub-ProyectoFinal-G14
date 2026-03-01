from typing import Optional
from poc1.domain.models.reservation import Reservation


class ReservationRepository:

    async def get_one_by_filter(self, filters: dict) -> Optional[Reservation]:
        """Devuelve una única Reservation o None. Usa get_or_none con los filtros proporcionados.
        Ej.: {'id': some_id} o {'user_id': uid}
        """
        filters = dict(filters or {})
        return await Reservation.get_or_none(**filters)

    async def list_by_filter(self, filters: dict) -> list[Reservation]:
        """Devuelve una lista de Reservation según filtros.

        Comportamiento:
        - Si filters contiene 'contain_only': usa los campos 'check_in' y 'check_out' para
          devolver reservas completamente contenidas en [check_in, check_out]
          (check_in__gte, check_out__lte).
        - En caso contrario, pasa los filtros tal cual a Reservation.filter(**filters).
        """
        filters = dict(filters or {})

        contain = filters.pop("contain_only", False)
        if contain:
            start = filters.pop("check_in", None)
            end = filters.pop("check_out", None)
            if not (start and end):
                raise ValueError("contain_only=True requiere 'check_in' y 'check_out')")
            # Aplicar filtro de contenido completo
            return await Reservation.filter(check_in__gte=start, check_out__lte=end, **filters)

        return await Reservation.filter(**filters)

    async def get_by_filter(self, filters: dict):
        """Compatibilidad: si se pasa 'id' devuelve un único objeto (Optional[Reservation]),
        en otro caso devuelve la lista (list[Reservation])."""
        filters = dict(filters or {})
        if "id" in filters:
            return await self.get_one_by_filter(filters)
        return await self.list_by_filter(filters)

    async  def create(self, **data) -> Reservation:
        """Crea una nueva Reservation con los datos proporcionados."""
        return await Reservation.create(**data)
