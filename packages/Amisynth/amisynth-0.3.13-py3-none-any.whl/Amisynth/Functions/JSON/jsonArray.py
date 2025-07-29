import xfox
from Amisynth.utils import json_storage

@xfox.addfunc(xfox.funcs)
async def jsonArray(*claves, **kwargs):
    if not claves:
        raise ValueError("❌ La función `$jsonArray` devolvió un error: Se esperaba un valor válido en la posición 1, pero se obtuvo un valor vacío.")
    
    data = json_storage
    
    try:
        for clave in claves[:-1]:
            if clave not in data or not isinstance(data[clave], dict):
                data[clave] = {}  # Crea el nivel si no existe
            data = data[clave]  # Avanza en la estructura del JSON
        
        ultima_clave = claves[-1]
        if ultima_clave not in data or not isinstance(data[ultima_clave], list):
            data[ultima_clave] = []  # Inserta el array vacío solo si no existe
        
        return ""
    except Exception as e:
        raise ValueError(f"❌ La función `$jsonArray` devolvió un error: {e}")
