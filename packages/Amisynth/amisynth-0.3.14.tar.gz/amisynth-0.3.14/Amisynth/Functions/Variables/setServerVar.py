import xfox
import discord
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def setServerVar(nombre=None, value=None, guild_id=None, *args, **kwargs):
    """Establece una variable para un servidor específico."""
    context = utils.ContextAmisynth()

    if nombre is None:
        raise ValueError("❌ La función `$setServerVar` devolvió un error: El argumento en la posición 1 está vacío o es inválido.")
    
    if value is None:
        raise ValueError("❌ La función `$setServerVar` devolvió un error: El argumento en la posición 2 está vacío o es inválido.")

    
    if guild_id is None:
        guild_id = context.guild_id

    var = utils.VariableManager()
    
    # Establece el valor para el servidor especificado
    var.set_value("guild", key=nombre, value=value, guild_id=guild_id)
    return ""