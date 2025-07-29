import xfox
from Amisynth.utils import embeds, valid_url  # Asumo que embeds es una lista global que estás usando

@xfox.addfunc(xfox.funcs)
async def authorIcon(url: str=None, indice:str= 1, *args, **kwargs):
    """
    Guarda un autor con ícono en la lista de embeds, con la URL del ícono y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param url: La URL del ícono que se quiere mostrar en el autor del embed.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$authorIcon` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args)+2}")
    
    if url is None:
        print("[DEBUG AUTHORICON] La funciom $authorIcon esta vacia.")
        raise ValueError("❌ La función `$authorIcon` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")
    
    if valid_url(url) == False:
        raise ValueError(f"❌ La función `$authorIcon` devolvió un error: se esperaba una URL en la posición 1, se obtuvo '{url}'")
    
    elif not indice is None:
        if not indice.isdigit():
            raise ValueError(f"❌ La función `$authorIcon` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")
    indice = int(indice)
    # Crear el embed con el autor y el ícono
    embed = {
        "author_icon": url,  # URL del ícono en el autor
        "index": indice      # Añadir el índice para identificar la posición
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo el author_icon
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            # Mantener los otros atributos del embed y solo actualizar el author_icon
            embeds[i]["author_icon"] = url
            break
    else:
        # Si no se encontró, agregar uno nuevo
        embeds.append(embed)

    return ""
