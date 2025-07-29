import xfox
from Amisynth.utils import embeds

@xfox.addfunc(xfox.funcs)
async def description(texto: str=None, indice:str="1", *args, **kwargs):
    """
    Guarda una descripción en la lista de embeds, con un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param texto: El texto de la descripción.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$description` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args)+2}")
    
    if texto is None:
        print("[DEBUG DESCRIPTION] La funciom $description esta vacia.")

        raise ValueError("❌ La función `$description` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")
    
    elif not indice is None:
        if not indice.isdigit():
            raise ValueError(f"❌ La función `$description` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")
    indice = int(indice)
    embed = {
        "description": texto,
        "index": indice  # Añadir el índice para identificar la posición
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo la descripción
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            # Mantener los otros atributos del embed y solo actualizar la descripción
            embeds[i]["description"] = texto
            break
    else:
        # Si no se encontró, agregar uno nuevo
        embeds.append(embed)

    return ""
