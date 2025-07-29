import discord
import xfox
import Amisynth.utils as utils

@xfox.addfunc(xfox.funcs)
async def sendMessage(texto, canal_id=None, retornar_id="false",*args, **kwargs): 
    n = utils.ContextAmisynth()
   
    if canal_id is None:
        canal = await n.get_channel(int(n.channel_id))  
       
    else:
        canal = await n.get_channel(int(canal_id))  
    
    if canal is None:
        raise ValueError(":x: Error en obtener el canal ID, Contacte con Soporte.")

    # Verificar si el canal es válido antes de enviar el mensaje
    if isinstance(canal, discord.TextChannel):
        mensaje = await canal.send(texto)
        if str(retornar_id).lower() == "true":
            return mensaje.id  # Retorna el ID del mensaje si se solicita
        
        return ""  # Retorna una cadena vacía si no se necesita el ID
    else:
        print(f"No se encontró un canal válido para enviar el mensaje. Canal ID: {canal_id}")


    print(f"No se encontró un canal válido para enviar el mensaje. Canal ID: {canal_id}")
    return None  # Indicar que falló el envío
