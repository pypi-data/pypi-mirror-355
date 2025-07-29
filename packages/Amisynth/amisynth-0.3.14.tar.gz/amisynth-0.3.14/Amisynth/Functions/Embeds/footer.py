import xfox
from Amisynth.utils import embeds  # Asegúrate de que 'embeds' sea una lista global compartida

@xfox.addfunc(xfox.funcs)
async def footer(texto_footer: str = None, indice: str = "1", *args, **kwargs):
    """
    Guarda un footer en la lista de embeds, con un texto de footer específico y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.

    :param texto_footer: El texto que se quiere mostrar en el footer del embed.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$footer` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args) + 2}")
    
    if texto_footer is None or texto_footer.strip() == "":
        print("[DEBUG FOOTER] La función $footer está vacía.")
        raise ValueError("❌ La función `$footer` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")
    
    # Validar y convertir el índice a entero
    if not indice.isdigit():
        raise ValueError(f"❌ La función `$footer` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")
    indice = int(indice)

    embed = {
        "footer": texto_footer,
        "index": indice
    }

    # Buscar si ya existe un embed con ese índice y actualizar solo el campo 'footer'
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            embeds[i]["footer"] = texto_footer
            break
    else:
        embeds.append(embed)

    return ""
