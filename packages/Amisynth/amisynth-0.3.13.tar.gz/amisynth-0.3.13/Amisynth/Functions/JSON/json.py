import xfox
from Amisynth.utils import json_storage
import asyncio

@xfox.addfunc(xfox.funcs)
async def json(*args, **kwargs):
    try:
        # Verifica que ningún argumento esté vacío, e indica la posición si lo está
        for i, arg in enumerate(args):
            if not str(arg).strip():
                raise ValueError(f"El argumento en la posición {i+1} está vacío o es inválido.")

        data = json_storage  # Inicia con el JSON base

        for clave in args:
            if isinstance(data, dict) and clave in data:
                data = data[clave]  # Acceder a clave en diccionario
            elif isinstance(data, list):
                try:
                    index = int(clave)  # Convertir clave a entero si es índice
                    data = data[index]  # Acceder a índice en lista
                except ValueError:
                    return f"El índice `{clave}` no es un número válido."
                except IndexError:
                    return f"El índice `{clave}` está fuera de rango."
            else:
                return f"La clave o índice `{clave}` no existe en el JSON."

        return data  # Devuelve el resultado final

    except Exception as e:
        raise ValueError(f"❌ La función `$json` devolvió un error: {str(e)}")
