import xfox
import discord
import Amisynth.utils as utils
@xfox.addfunc(xfox.funcs)
async def customID(*args, **kwargs):
    n = utils.ContextAmisynth().custom_id
    if args:
        raise ValueError(f"❌ La función `$customID` devolvió un error: demasiados argumentos, no se esperaban argumentos, se obtuvieron {len(args)}")
    return n
