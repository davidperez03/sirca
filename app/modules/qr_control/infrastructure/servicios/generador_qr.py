import qrcode
import io
import base64
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

class GeneradorQR:
    def __init__(self):
        self.tamaño_base = 10
        self.border = 4
        
    def generar_qr_imagen(self, datos: str, logo_path: Optional[str] = None) -> str:
        """Genera un QR code como imagen base64"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=self.tamaño_base,
            border=self.border,
        )
        
        qr.add_data(datos)
        qr.make(fit=True)
        
        # Crear imagen del QR
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Añadir logo si se proporciona
        if logo_path:
            img = self._añadir_logo(img, logo_path)
        
        # Convertir a base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    def _añadir_logo(self, qr_img: Image.Image, logo_path: str) -> Image.Image:
        """Añade logo en el centro del QR"""
        try:
            logo = Image.open(logo_path)
            
            # Calcular tamaño del logo (10% del QR)
            qr_width, qr_height = qr_img.size
            logo_size = int(min(qr_width, qr_height) * 0.1)
            
            # Redimensionar logo
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Crear máscara circular para el logo
            mask = Image.new('L', (logo_size, logo_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_size, logo_size), fill=255)
            
            # Aplicar máscara
            logo.putalpha(mask)
            
            # Calcular posición central
            pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            
            # Pegar logo
            qr_img.paste(logo, pos, logo)
            
        except Exception as e:
            print(f"Error añadiendo logo: {e}")
        
        return qr_img