import requests
import time
from datetime import datetime

ENDPOINT = "https://app.travel-hub.tech/service-core/version"
OLD_VERSION = "0.3"
NEW_VERSION = "0.3.1"

print(f"Chequeando {ENDPOINT} cada segundo hasta que cambie de {OLD_VERSION} a {NEW_VERSION}...")

start_time = datetime.now()
switched = False
new_version_time = None

while True:
    try:
        r = requests.get(ENDPOINT, timeout=3)
        data = r.json()
        version = data.get("version")
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] version: {version}")

        # Detecta que la versión cambia a la nueva
        if not switched and version == NEW_VERSION:
            new_version_time = datetime.now()
            elapsed = (new_version_time - start_time).total_seconds()
            print(f"\n¡Versión actualizada detectada! Tiempo transcurrido: {elapsed:.2f} segundos")
            print("Esperando para ver si ocurre un rollback a la versión anterior...\n")
            switched = True

        # Detecta que regresó a la versión vieja (rollback)
        if switched and version == OLD_VERSION:
            rollback_time = datetime.now()
            rollback_elapsed = (rollback_time - new_version_time).total_seconds()
            print(f"\n¡Rollback detectado! Volvió a la versión anterior después de {rollback_elapsed:.2f} segundos con la nueva versión activa.")
            break

    except Exception as e:
        print(f"Error al consultar: {e}")
    time.sleep(1)

if not switched:
    print("\nLa versión nueva nunca apareció durante la prueba. ¡No hubo cambio ni rollback!")