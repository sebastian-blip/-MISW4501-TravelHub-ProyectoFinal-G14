"""
Máquina de estados flexible con historial de navegación.
Permite saltar entre cualquier paso (1, 2, 3, 4).
"""
from typing import List
import json


# Todos los estados disponibles (1-4)
ALL_STATES = [1, 2, 3, 4]

# Nombres de pasos para mostrar
STEP_NAMES = {
    1: "step_one",
    2: "step_two", 
    3: "step_three",
    4: "step_four"
}


class TaskStateMachine:
    """
    Máquina de estados flexible que permite saltar entre cualquier paso.
    
    Pasos disponibles: 1, 2, 3, 4
    
    Características:
        - Permite transición desde cualquier paso a cualquier paso
        - Mantiene historial de pasos visitados
        - Evita duplicados consecutivos en  el historial
    """
    
    def __init__(self, initial_step: int = 1, history: List[int] = None):
        if initial_step not in ALL_STATES:
            raise ValueError(f"Paso inicial {initial_step} no válido. Use: {ALL_STATES}")
        
        self._current_step = initial_step
        # Inicializar historial
        if history is None:
            self._history = [initial_step]
        else:
            self._history = list(history)
    
    @property
    def step(self) -> int:
        """Retorna el paso actual (1-4)."""
        return self._current_step
    
    @property
    def state(self) -> str:
        """Retorna el nombre del estado actual (step_one, etc.)."""
        return STEP_NAMES.get(self._current_step, "unknown")
    
    @property
    def history(self) -> List[int]:

        """Retorna el historial de pasos visitados."""
        return self._history.copy()
    
    def get_history_json(self) -> str:
        """Retorna el historial como string JSON."""
        return json.dumps(self._history)
    
    @staticmethod
    def parse_history(history_json: str) -> List[int]:
        """Parsea el historial desde string JSON."""
        try:
            parsed = json.loads(history_json)
            # Asegurar que sea lista de enteros
            return [int(x) for x in parsed]
        except (json.JSONDecodeError, TypeError, ValueError):
            return [1]
    
    def jump_to(self, target_step: int) -> bool:
        """
        Salta a cualquier paso válido (1-4).
        
        Args:
            target_step: Número de paso destino (1, 2, 3, o 4)
            
        Returns:
            True si el salto fue exitoso
            
        Raises:
            ValueError: Si el paso destino no es válido
        """
        if target_step not in ALL_STATES:
            raise ValueError(f"Paso '{target_step}' no válido. Pasos válidos: {ALL_STATES}")
        
        # Si es el mismo paso, no agregar al historial
        if self._current_step == target_step:
            print(f"[StateMachine] Ya estás en el paso {target_step}")
            return False
        
        # Actualizar paso
        previous_step = self._current_step
        self._current_step = target_step
        
        # Agregar al historial
        self._history.append(target_step)
        
        print(f"[StateMachine] Salto: {previous_step} → {target_step}")
        print(f"[StateMachine] Historial: {self._history}")
        
        return True
    
    def go_back(self) -> bool:
        """
        Retrocede al paso anterior en el historial.
        
        Returns:
            True si pudo retroceder, False si no hay historial previo
        """
        if len(self._history) < 2:
            print("[StateMachine] No hay pasos anteriores en el historial")
            return False
        
        # Remover paso actual del historial
        self._history.pop()
        
        # Volver al paso anterior
        previous_step = self._history[-1]
        current = self._current_step
        self._current_step = previous_step
        
        print(f"[StateMachine] Retrocediendo: {current} → {previous_step}")
        print(f"[StateMachine] Historial: {self._history}")
        
        return True
    
    def get_available_transitions(self) -> List[int]:
        """Retorna todos los pasos disponibles para saltar (excepto el actual)."""
        return [s for s in ALL_STATES if s != self._current_step]
    
    def can_jump_to(self, target_step: int) -> bool:
        """Verifica si se puede saltar al paso destino."""
        return target_step in ALL_STATES and target_step != self._current_step
