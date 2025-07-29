import xfox
from Amisynth.utils import embeds  # Asumo que embeds es una lista global que estás usando

@xfox.addfunc(xfox.funcs)
async def title(texto_title: str = None, indice: int = 1, *args, **kwargs):
    """
    Guarda un título en la lista de embeds, con un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param texto_title: El texto que se quiere mostrar como título en el embed.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$title` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args)+2}")

    if texto_title is None or texto_title.strip() == "":
        print("[DEBUG TITLE] La función $title está vacía")
        raise ValueError("❌ La función `$title` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")

    # Validar que el índice sea un número entero
    if not isinstance(indice, int):
        try:
            indice = int(indice)
        except (ValueError, TypeError):
            raise ValueError(f"❌ La función `$title` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")

    embed = {
        "title": texto_title,
        "index": indice
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo el título
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["title"] = texto_title
            break
    else:
        # Si no se encontró, agregar uno nuevo
        embeds.append(embed)

    return ""
