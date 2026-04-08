"""
Máquina de estados con Meta-clase para gestión de estados nombrados.
Estados: validate → create → cancelation (con saltos permitidos)
"""
from typing import List, Callable, Dict, Optional
import json


class Meta:
    """
    Metaclase que define los estados disponibles y sus funciones asociadas.
    """
    # Estados disponibles
    VALIDATE = "validate"
    CREATE = "create"
    CANCELATION = "cancelation"
    
    # Lista de todos los estados
    ALL_STATES = [VALIDATE, CREATE, CANCELATION]
    
    # Descripciones de cada estado
    DESCRIPTIONS = {
        VALIDATE: "Validación de usuario y permisos",
        CREATE: "Creación y procesamiento de datos",
        CANCELATION: "Cancelación o finalización"
    }
    
    # Funciones asociadas a cada estado (se pueden sobreescribir)
    FUNCTIONS: Dict[str, List[str]] = {
        VALIDATE: ["check_user_exists", "verify_permissions"],
        CREATE: ["save_to_database", "process_data"],
        CANCELATION: ["cleanup_resources", "send_notification"]
    }


class TaskStateMachine:
    """
    Máquina de estados con estados nombrados (validate, create, cancelation).
    
    Permite saltos entre cualquier estado.
    Cada estado tiene funciones asociadas definidas en Meta.
    """
    
    def __init__(self, initial_state: str = Meta.VALIDATE, history: List[str] = None):
        if initial_state not in Meta.ALL_STATES:
            raise ValueError(f"Estado '{initial_state}' no válido. Use: {Meta.ALL_STATES}")
        
        self._current_state = initial_state
        self._meta = Meta()
        
        # Inicializar historial
        if history is None:
            self._history = [initial_state]
        else:
            self._history = list(history)
    
    @property
    def state(self) -> str:
        """Retorna el estado actual."""
        return self._current_state
    
    @property
    def history(self) -> List[str]:
        """Retorna el historial de estados visitados."""
        return self._history.copy()
    
    def get_history_json(self) -> str:
        """Retorna el historial como string JSON."""
        return json.dumps(self._history)
    
    @staticmethod
    def parse_history(history_json: Optional[str]) -> List[str]:
        """Parsea el historial desde string JSON."""
        try:
            parsed = json.loads(history_json)
            return [str(x) for x in parsed]
        except (json.JSONDecodeError, TypeError, ValueError):
            return [Meta.VALIDATE]
    
    def get_available_transitions(self) -> List[str]:
        """Retorna todos los estados disponibles para saltar (excepto el actual)."""
        return [s for s in Meta.ALL_STATES if s != self._current_state]
    
    def get_available_functions(self) -> List[str]:
        """Retorna las funciones disponibles para el estado actual."""
        return Meta.FUNCTIONS.get(self._current_state, [])
    
    def get_description(self) -> str:
        """Retorna la descripción del estado actual."""
        return Meta.DESCRIPTIONS.get(self._current_state, "Sin descripción")
    
    def transition_to(self, target_state: str) -> bool:
        """
        Transiciona a cualquier estado válido.
        Permite "re-ejecutar" el mismo estado (útil para refrescar/re-procesar).
        
        Args:
            target_state: Nombre del estado destino (validate, create, cancelation)
            
        Returns:
            True si la transición fue exitosa
        """
        if target_state not in Meta.ALL_STATES:
            raise ValueError(f"Estado '{target_state}' no válido. Estados: {Meta.ALL_STATES}")
        
        # Guardar estado anterior
        previous_state = self._current_state
        
        # Ejecutar función de salida (siempre, incluso si es el mismo estado)
        self._on_exit_state(previous_state)
        
        # Actualizar estado (puede ser el mismo o diferente)
        self._current_state = target_state
        
        # Siempre agregar al historial (incluso si es el mismo estado, para trackear re-ejecuciones)
        self._history.append(target_state)
        
        # Ejecutar función de entrada (siempre, para re-ejecutar funciones del estado)
        self._on_enter_state(target_state)
        
        if previous_state == target_state:
            print(f"[StateMachine] Re-ejecutando estado: '{target_state}'")
        else:
            print(f"[StateMachine] Transición: '{previous_state}' → '{target_state}'")
        print(f"[StateMachine] Historial: {self._history}")
        print(f"[StateMachine] Funciones disponibles: {self.get_available_functions()}")
        
        return True
    
    def _on_enter_state(self, state: str):
        """Callback ejecutado al entrar a un estado."""
        print(f"[StateMachine] → Entrando a '{state}': {Meta.DESCRIPTIONS.get(state)}")
        
        # Aquí se pueden ejecutar acciones automáticas según el estado
        if state == Meta.VALIDATE:
            print(f"[StateMachine]   Acción: Validando usuario...")
        elif state == Meta.CREATE:
            print(f"[StateMachine]   Acción: Creando registros...")
        elif state == Meta.CANCELATION:
            print(f"[StateMachine]   Acción: Procesando cancelación...")
    
    def _on_exit_state(self, state: str):

        print(f"[StateMachine] ← Saliendo de '{state}'")
    
    def go_back(self) -> bool:

        if len(self._history) < 2:
            print("[StateMachine] No hay estados anteriores")
            return False
        

        self._history.pop()
        

        previous_state = self._current_state
        new_state = self._history[-1]
        self._current_state = new_state
        
        print(f"[StateMachine] Retrocediendo: '{previous_state}' → '{new_state}'")
        
        return True
    
    def can_transition_to(self, target_state: str) -> bool:

        return target_state in Meta.ALL_STATES and target_state != self._current_state
    
    def execute_function(self, function_name: str) -> bool:
        """
        Ejecuta una función específica del estado actual.
        
        Args:
            function_name: Nombre de la función a ejecutar
            
        Returns:
            True si la función existe y se ejecutó
        """
        available_functions = self.get_available_functions()
        
        if function_name not in available_functions:
            print(f"[StateMachine] Función '{function_name}' no disponible en estado '{self._current_state}'")
            return False
        
        # Aquí se ejecutaría la lógica real de la función
        print(f"[StateMachine] Ejecutando función '{function_name}' en estado '{self._current_state}'")
        return True


# Funciones de conveniencia para los estados
def get_state_machine(initial_state: str = Meta.VALIDATE, history: List[str] = None) -> TaskStateMachine:
    """Factory function para crear una máquina de estados."""
    return TaskStateMachine(initial_state, history)
