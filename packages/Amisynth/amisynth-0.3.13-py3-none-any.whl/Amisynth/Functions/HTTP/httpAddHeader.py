import aiohttp
import xfox
import Amisynth.utils as utils

# Función para agregar headers a las solicitudes HTTP
@xfox.addfunc(xfox.funcs)
async def httpAddHeader(key: str, value: str, *args, **kwargs):
    """Agrega un header a la solicitud HTTP para las solicitudes POST/PUT/PATCH."""

    if not key:
        raise ValueError("❌ La función `$httpAddHeader` devolvió un error:  No se obtuvo nada en el argumento 1")
    
    elif not value:
        raise ValueError("❌ La función `$httpAddHeader` devolvió un error:  No se obtuvo nada en el argumento 2")
    

    if "headers" not in utils.http_data:
        utils.http_data["headers"] = {}

    # Añadir el header al diccionario de headers
    utils.http_data["headers"][key] = value
    print(F"[DEBUG HTTPADDHEADER] Header '{key}: {value}' añadido a la solicitud.")
    return f""
