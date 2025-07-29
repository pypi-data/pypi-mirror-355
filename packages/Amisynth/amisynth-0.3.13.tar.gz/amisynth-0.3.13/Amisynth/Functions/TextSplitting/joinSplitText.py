import xfox
from Amisynth.Functions.storage import split_storage  # Importamos el almacenamiento global


@xfox.addfunc(xfox.funcs)
async def joinSplitText(separator: str=None, *args, **kwargs):
    global split_storage
    if separator is None:
        raise ValueError("❌ La función `$joinSplitText` devolvió un error: Se esperaba un valor válido en la posición 1, pero se obtuvo un valor vacío.")
    if "last_split" not in split_storage:
        raise ValueError("❌ La función `$joinSplitText` devolvió un error: Aún no se ha dividido ningún texto.")
    
    return separator.join(split_storage.get("last_split", []))