import xfox
import discord
import Amisynth.utils as utils
@xfox.addfunc(xfox.funcs)
async def getServerVar(nombre:str=None, guild_id:str=None, *args, **kwargs):
    """Obtiene una variable para un servidor específico."""
    context = kwargs["ctx" ]
    
    if nombre is None:
        raise ValueError("❌ La función `$getServerVar` devolvió un error: El argumento en la posición 1 está vacío o es inválido.")
    
    if guild_id is None:
        guild_id = context.guild_id or context.guild.id

    var = utils.VariableManager()

    # Obtiene el valor para el servidor especificado
    value = var.get_value("guild", key=nombre, guild_id=guild_id)
    
    if value is None:
        return f"❌ La función `$getServerVar` devolvió un error: No se encontró la variable `{nombre}` para el servidor especificado."
    
    return value