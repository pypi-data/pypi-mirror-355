import xfox

@xfox.addfunc(xfox.funcs)
async def ping(*args, **kwargs):
    from Amisynth.utils import bot_inst
    bot = bot_inst
    if not bot:
        raise ValueError("❌ La función `$ping` devolvió un error: El objeto `bot` no está disponible en `$ping[]`.")
    if args:
        raise ValueError("❌ La función `$ping` devolvió un error: No es obligatorio poner argumentos con contenido.")
    latency_ms = round(bot.latency * 1000)
    return f"{latency_ms}"
