import aiohttp
import xfox
import Amisynth.utils as utils
import ast

# Función para HTTP POST
@xfox.addfunc(xfox.funcs)
async def httpDelete(url: str, json: str, *args, **kwargs):
    """Realiza una solicitud HTTP POST con el cuerpo JSON especificado."""
    try:
        # Usamos ast.literal_eval para analizar de forma segura el JSON
        json = ast.literal_eval(json)  # Convertimos la entrada a un valor literal seguro

        async with aiohttp.ClientSession() as session:
            async with session.delete(url, json=json, headers=utils.http_data["headers"]) as response:
                response.raise_for_status()  # Lanza error si hay un problema
                # Almacenar la respuesta JSON en una variable global
                utils.http_response = await response.json()  # Asumiendo que la respuesta es JSON
                utils.http_status = await response.status
                print("[DEBUG HTTPOST] Solicitud POST realizada con éxito.")
                return ""
    except Exception as e:
        return f"Error en $httpPost: {str(e)}"
