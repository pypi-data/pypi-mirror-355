import xfox
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def channelName(channel_id: str, *args, **kwargs):
    context = utils.ContextAmisynth()
    guild = context.obj_guild

    if guild is None:
        print("[DEBUG CHANNELNAME] No se puede usar fuera de un servidor.")
        raise ValueError("❌ La función `$channelName` devolvió un error: No se puede usar fuera de un servidor.")

    if not channel_id.isdigit():
        print(f"[DEBUG CHANNELNAME] ID inválido: {channel_id}")
        raise ValueError(f"❌ La función `$channelName` devolvió un error: Se esperaba un entero en la posición 1, obtuve '{channel_id}'")

    channel = guild.get_channel(int(channel_id))
    if channel:
        print(f"[DEBUG CHANNELNAME] Canal encontrado: {channel.name}")
        return channel.name

    print("[DEBUG CHANNELNAME] Canal no encontrado")
    raise ValueError("❌ La función `$channelName` devolvió un error: Canal no encontrado en la posicion 1.", )
