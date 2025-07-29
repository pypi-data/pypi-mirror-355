import xfox
from Amisynth.utils import embeds  # Asumo que embeds es una lista global
from Amisynth.utils import valid_url

@xfox.addfunc(xfox.funcs)
async def titleURL(url: str, indice: int = 1, *args, **kwargs):
    """
    Guarda una URL en el título del embed, con un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param url: La URL que se quiere asociar al título del embed.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$titleURL` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args)+2}")

    if url is None or url.strip() == "":
        print("[DEBUG TITLEURL] La función $titleURL está vacía.")
        raise ValueError("❌ La función `$titleURL` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")

    if not valid_url(url):
        raise ValueError(f"❌ La función `$titleURL` devolvió un error: se esperaba una URL válida en la posición 1, se obtuvo '{url}'")

    # Validar y convertir el índice a entero si no lo es
    if not isinstance(indice, int):
        try:
            indice = int(indice)
        except (ValueError, TypeError):
            raise ValueError(f"❌ La función `$titleURL` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")

    # Crear el embed con la URL en el título
    embed = {
        "title_url": url,
        "index": indice
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo la URL del título
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["title_url"] = url
            break
    else:
        embeds.append(embed)

    return ""
