import asyncio
from typing import List
from datetime import datetime
from app.modules.qr_control.domain.entidades.registro_acceso import RegistroAcceso
from app.modules.auth.blacklist import get_redis

class NotificadorAccesos:
    def __init__(self):
        self.redis_client = get_redis()
        
    async def notificar_acceso_tiempo_real(self, registro: RegistroAcceso) -> None:
        """Notifica acceso en tiempo real via WebSocket/SSE"""
        try:
            # Publicar evento en Redis para WebSockets
            evento = {
                "tipo": "nuevo_acceso",
                "timestamp": registro.fecha_hora.isoformat(),
                "usuario": f"{registro.usuario.nombres.valor} {registro.usuario.apellidos.valor}",
                "usuario_id": registro.usuario.numero_documento.valor,
                "movimiento": registro.tipo_movimiento,
                "vigilante": registro.vigilante_id,
                "items": len(registro.items_declarados)
            }
            
            # Canal para dashboard de vigilancia
            await self._publicar_redis("sirca:accesos", evento)
            
            # Canal específico por usuario (para notificaciones personales)
            await self._publicar_redis(f"sirca:user:{registro.usuario.numero_documento.valor}", evento)
            
        except Exception as e:
            print(f"Error notificando acceso: {e}")
    
    async def _publicar_redis(self, canal: str, datos: dict) -> None:
        """Publica evento en Redis"""
        try:
            import json
            self.redis_client.publish(canal, json.dumps(datos))
        except Exception as e:
            print(f"Error publicando en Redis: {e}")
    
    def obtener_accesos_recientes(self, minutos: int = 30) -> List[dict]:
        """Obtiene accesos recientes desde Redis cache"""
        try:
            import json
            key = f"sirca:accesos_recientes:{minutos}"
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
        return []
    
    def cachear_accesos_recientes(self, accesos: List[RegistroAcceso], minutos: int = 30) -> None:
        """Cachea accesos recientes en Redis"""
        try:
            import json
            key = f"sirca:accesos_recientes:{minutos}"
            
            # Convertir a dict para JSON
            accesos_dict = []
            for acc in accesos:
                accesos_dict.append({
                    "id": acc.id,
                    "usuario": f"{acc.usuario.nombres.valor} {acc.usuario.apellidos.valor}",
                    "usuario_id": acc.usuario.numero_documento.valor,
                    "tipo": acc.tipo_movimiento,
                    "fecha": acc.fecha_hora.isoformat(),
                    "vigilante": acc.vigilante_id,
                    "items": len(acc.items_declarados)
                })
            
            # Cachear por 5 minutos
            self.redis_client.setex(key, 300, json.dumps(accesos_dict))
            
        except Exception as e:
            print(f"Error cacheando accesos: {e}")