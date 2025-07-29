import xfox
from Amisynth.utils import embeds, valid_url

@xfox.addfunc(xfox.funcs)
async def authorURL(url: str=None, indice:str=1, *args, **kwargs):
    """
    Guarda un autor con ícono en la lista de embeds, con la URL del ícono y un índice opcional.
    Si se especifica el índice, se inserta o actualiza en esa posición. Si no, se agrega en la posición 1.
    
    :param url: La URL del ícono que se quiere mostrar en el autor del embed.
    :param indice: El índice opcional del embed (posición en la lista).
    """
    if args:
        raise ValueError(f"❌ La función `$authorURL` devolvió un error: demasiados argumentos, se esperaban hasta 2, se obtuvieron {len(args)+2}")
    
    if url is None:
        print("[DEBUG AUTHORURL] La funciom $authorURL esta vacia.")
        raise ValueError("❌ La función `$authorURL` devolvió un error: se esperaba un valor válido en la posición 1, se obtuvo un valor vacío")
    
    if valid_url(url) == False:
        raise ValueError(f"❌ La función `$authorURL` devolvió un error: se esperaba una URL en la posición 1, se obtuvo '{url}'")
    
    elif not indice is None:
        if not indice.isdigit():
            raise ValueError(f"❌ La función `$authorURL` devolvió un error: se esperaba un entero en la posición 2, se obtuvo '{indice}'")
    
    indice = int(indice)
    embed = {
        "author_url": url, 
        "index": indice     
    }

   
    for i, item in enumerate(embeds):
        if item.get("index") == indice:
            # Mantener los otros atributos del embed y solo actualizar el author_url
            embeds[i]["author_url"] = url
            break
    else:
        # Si no se encontró, agregar uno nuevo
        embeds.append(embed)

    return ""
