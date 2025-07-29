
import xfox
import discord
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def getChannelVar(nombre:str=None, guild_id:str=None, channel_id:str=None, *args, **kwargs):
    """Obtiene una variable para un canal específico."""
    context = utils.ContextAmisynth()
    
    if nombre is None:
        raise ValueError("❌ La función `$getChannelVar` devolvió un error: El argumento en la posición 1 está vacío o es inválido.")
    
    if guild_id is None:
        guild_id = context.guild_id

    if channel_id is None:
        channel_id = context.channel_id

    var = utils.VariableManager()

    # Obtiene el valor para el canal especificado
    value = var.get_value("channel", key=nombre, guild_id=guild_id, channel_id=channel_id)
    
    if value is None:
        return f"❌ La función `$getChannelVar` devolvió un error: No se encontró la variable `{nombre}` para el canal especificado."
    
    return value