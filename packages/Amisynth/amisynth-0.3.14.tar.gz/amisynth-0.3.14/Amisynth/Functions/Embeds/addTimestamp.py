import xfox
from Amisynth.utils import embeds  # Asumo que embeds es una lista global que estás usando
from datetime import datetime
@xfox.addfunc(xfox.funcs)
async def addTimestamp(indice:str=1, *args, **kwargs):
    """
    Agrega un timestamp en la lista de embeds con un índice opcional.
    Si no se especifica el índice, se agrega en la posición 1.
    
    :param args: Argumentos opcionales, el primer argumento será el índice.
    """
    if args:
        raise ValueError(f"❌ La función `$addTimestamp` devolvió un error: demasiados argumentos, se esperaban hasta 1, se obtuvieron {len(args)+1}")
    
    if not indice:
        if not indice.isdigit():
            raise ValueError(f"❌ La función `$addTimestamp` devolvió un error: se esperaba un entero en la posición 1, se obtuvo '{indice}'")
    
    embed = {
        "timestamp": "true", 
        "index": int(indice)          
    }

    # Buscar si ya existe un embed con ese índice y actualizarlo
    for i, item in enumerate(embeds):
        if item.get("index") == int(indice):
            # Actualizamos el embed solo si el índice coincide
            embeds[i]["timestamp"] = "true"  # Aquí puedes poner lo que quieras actualizar
            break
    else:
        # Si no se encontró, agregamos un nuevo embed con ese índice
        embeds.append(embed)

    return ""
