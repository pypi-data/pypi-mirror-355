import xfox
import discord
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def setPrefix(prefix: str, guild_id: int = None, *args, **kwargs):
    context = utils.ContextAmisynth(*args, **kwargs)
    bot = utils.bot_inst

    if not prefix:
        raise ValueError("❌ La función `$setPrefix` devolvió un error: Debes especificar un prefijo en el argumento.")

    if guild_id is not None and not isinstance(guild_id, int):
        raise ValueError(f"❌ La función `$setPrefix` devolvió un error: El ID del servidor `{guild_id}` no es válido.")

    if guild_id is None:
        guild_id = context.guild_id

    bot.set_prefijo_servidor(guild_id, prefix)
    return ""
