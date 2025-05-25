# 🚦 SIRCA - Sistema de Registro, Control y Acceso

**SIRCA** es un sistema en **desarrollo** orientado a la gestión integral de:

- Usuarios y su información personal.
- Vehículos registrados.
- Pertenencias asociadas.
- Control de ingreso y salida institucional.
- Seguridad y validación de accesos.
- Análisis de datos y detección de tendencias.

---

## 🎯 Objetivo

**Simplificar** y **asegurar** el control de acceso a organizaciones, validando usuarios, vehículos y pertenencias, mientras se recopilan datos que serán utilizados para:

- 🔍 Análisis de comportamiento.
- 🛡️ Seguridad interna.

---

## 🚧 Estado Actual del Proyecto

### ✅ Autenticación y Seguridad
- [x] Registro de usuarios con autenticación segura  
- [x] Activación de cuentas mediante enlace por correo electrónico  
- [x] Recuperación de contraseña con JWT y Redis  
- [x] Blacklist de tokens JWT (logout y tokens usados)  
- [ ] Rate limiting para prevenir abusos en login y recuperación  
- [ ] Registro de intentos fallidos y bloqueo temporal  
- [ ] Auditoría de inicios de sesión y acciones sensibles  

### 🚗 Gestión de Vehículos y Pertenencias
- [ ] Modelo de datos para asociar vehículos a usuarios  
- [ ] Registro detallado de pertenencias por usuario  
- [ ] Lógica de ingreso, cesión y retiro de vehículos  
- [ ] Historial de movimientos por vehículo/pertenencia  
- [ ] Validaciones para evitar duplicados (placas, objetos)  

### 🚪 Control de Ingreso y Salida
- [ ] Escaneo de códigos QR por personal autorizado (validación en tiempo real)  
- [ ] Alerta ante accesos no autorizados  
- [ ] Registro de errores en lectura o intentos inválidos  
- [ ] Exportación de registros para auditoría  

### 📊 Dashboard y Análisis de Datos
- [ ] Panel administrativo con resumen de actividad general  
- [ ] Análisis de comportamiento: frecuencia, horarios pico, usuarios activos  
- [ ] Alertas basadas en patrones sospechosos  
- [ ] Comparativas por sector, tipo de usuario o vehículo  
- [ ] Métricas logísticas: tiempos de acceso, congestión  
- [ ] Exportación de reportes en Excel y PDF  
- [ ] Visualizaciones: mapas de calor, gráficas de barras y líneas  

### 🔐 Seguridad Interna y Trazabilidad
- [ ] Registro completo de acciones por usuario (CRUD, accesos)  
- [ ] Revisión y reversión de eventos críticos  
- [ ] Cifrado de datos sensibles (en tránsito y almacenamiento)  
- [ ] Control de permisos y accesos según roles definidos  
- [ ] Notificaciones al administrador ante cambios críticos  

> 💡 **Nota**: Este proyecto se encuentra en fase activa de desarrollo (`desarrollo` branch).

---

## ⚙️ Tecnologías Utilizadas

- 🐍 **Python 3.12**
- 🚀 **FastAPI**
- 🛢️ **SQLAlchemy** + **SQLite** (en local, con PostgreSQL planeado)
- 🔐 **JWT Authentication**
- 📦 **Redis** para Blacklist de tokens
- 🐳 **Docker** + **Docker Compose**
- 🎨 **Jinja2** para plantillas HTML
- 💻 **Bootstrap 5** para el frontend

---

## 🧪 Instalación y Despliegue

### 🚀 Ejecución con Docker

  ```bash
  docker-compose up --build
  ```

## 🔒 Seguridad actual

  - Tokens de activación de cuenta via correo, con expiración segura.
  - Tokens de recuperación de contraseña, invalidados tras un solo uso.
  - Manejo de sesiones con Redis para blacklists de JWT.
  - Protección contra reuse de tokens expuestos.

## 📋 Plan futuro de módulos

  - 🚗 Gestión de Vehículos.
  - 🛍️ Gestión de Pertenencias.
  - 📊 Dashboard de Tendencias de Uso.
  - 🛡️ Módulo de Seguridad y Bloqueo Temporal.
  - 📈 Análisis predictivo de tráfico de usuarios.

    ---

    ## 👨‍💻 Autor

    - **David P.** – Backend Developer