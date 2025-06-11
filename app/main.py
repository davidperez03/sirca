'''
    Punto de entrada para la aplicación FastAPI.
    Configura la app, monta archivos estáticos, crea las tablas de la base de datos e incluye los routers de los módulos.
'''
# Importaciones de terceros
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


import os
import sqlite3
from datetime import datetime
from pathlib import Path
from sqlalchemy import text
import traceback


# Configuración principal
from app.core.config import settings
from app.core.dependencias.dependencias import engine, Base

# Routers de la aplicación
from app.modules.autenticacion.interface.rutas import router as usuarios_router
from app.modules.pertenencias.interface.rutas import router as pertenencias_router
from app.modules.vehiculos.interface.rutas import router as vehiculos_router


app = FastAPI(title=settings.app_name, debug=settings.debug)


Base.metadata.create_all(bind=engine)

# Configuración de plantillas
app.mount("/static", StaticFiles(directory="app/core/resources/static"), name="static")
app.mount("/media", StaticFiles(directory="app/core/resources/media"), name="media")

templates = Jinja2Templates(directory="app/core/resources/templates")

# Montar el router de usuarios
app.include_router(usuarios_router)

# Montar otros routers de módulos aquí
app.include_router(pertenencias_router)
app.include_router(vehiculos_router)

# Ruta raíz
@app.get("/", response_class=HTMLResponse)
def inicio(request: Request):
    return templates.TemplateResponse("inicio.html", {"request": request})

@app.get("/health")
async def health_check():
    """Endpoint básico de salud"""
    return {
        "status": "✅ API funcionando",
        "timestamp": datetime.now().isoformat(),
        "environment": "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
    }

@app.get("/diagnostics/storage")
async def diagnostics_storage():
    """Diagnóstico completo del almacenamiento"""
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "is_railway": bool(os.getenv("RAILWAY_ENVIRONMENT")),
                "railway_env": os.getenv("RAILWAY_ENVIRONMENT", "Not set"),
                "port": os.getenv("PORT", "Not set")
            },
            "database": {},
            "redis": {},
            "filesystem": {},
            "config": {}
        }
        
        # === DIAGNÓSTICO DE BASE DE DATOS ===
        try:
            database_url = str(settings.database_url)
            results["database"]["url"] = database_url[:50] + "..." if len(database_url) > 50 else database_url
            results["database"]["type"] = "PostgreSQL" if "postgresql" in database_url.lower() else "SQLite"
            
            # Test de conexión
            from app.core.dependencias.dependencias import engine
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test")).fetchone()
                results["database"]["connection"] = "✅ Conectado"
                results["database"]["test_query"] = f"✅ {result[0]}"
                
                # Contar tablas
                if "postgresql" in database_url.lower():
                    tables_result = conn.execute(text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                    )).fetchall()
                else:
                    tables_result = conn.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )).fetchall()
                
                results["database"]["tables"] = [row[0] for row in tables_result]
                results["database"]["table_count"] = len(tables_result)
                
                # Contar usuarios si existe la tabla
                try:
                    user_count = conn.execute(text("SELECT COUNT(*) FROM usuarios")).fetchone()
                    results["database"]["usuarios_count"] = user_count[0]
                except Exception as e:
                    results["database"]["usuarios_count"] = f"❌ Error: {str(e)}"
                
                # Contar pertenencias si existe la tabla
                try:
                    pert_count = conn.execute(text("SELECT COUNT(*) FROM pertenencias")).fetchone()
                    results["database"]["pertenencias_count"] = pert_count[0]
                except Exception as e:
                    results["database"]["pertenencias_count"] = f"❌ Error: {str(e)}"
                
                # Contar vehículos si existe la tabla
                try:
                    veh_count = conn.execute(text("SELECT COUNT(*) FROM vehiculos")).fetchone()
                    results["database"]["vehiculos_count"] = veh_count[0]
                except Exception as e:
                    results["database"]["vehiculos_count"] = f"❌ Error: {str(e)}"
                    
        except Exception as e:
            results["database"]["connection"] = f"❌ Error: {str(e)}"
            results["database"]["error_detail"] = traceback.format_exc()
        
        # === DIAGNÓSTICO DE REDIS ===
        try:
            from app.modules.auth.blacklist import get_redis
            redis_client = get_redis()
            
            # Test básico
            redis_client.ping()
            results["redis"]["connection"] = "✅ Conectado"
            
            # Test de escritura/lectura
            test_key = f"test:{datetime.now().timestamp()}"
            redis_client.setex(test_key, 10, "test_value")
            test_read = redis_client.get(test_key)
            results["redis"]["write_test"] = "✅ Escritura OK"
            results["redis"]["read_test"] = f"✅ Lectura OK: {test_read}"
            
            # Limpiar
            redis_client.delete(test_key)
            
            # Contar keys
            all_keys = redis_client.keys("*")
            results["redis"]["total_keys"] = len(all_keys)
            results["redis"]["blacklist_keys"] = len([k for k in all_keys if k.startswith("blacklist:")])
            results["redis"]["jwt_keys"] = len([k for k in all_keys if k.startswith("jwt:")])
            
        except Exception as e:
            results["redis"]["connection"] = f"❌ Error: {str(e)}"
            results["redis"]["error_detail"] = traceback.format_exc()
        
        # === DIAGNÓSTICO DEL SISTEMA DE ARCHIVOS ===
        try:
            # Directorio actual
            current_dir = Path.cwd()
            results["filesystem"]["current_directory"] = str(current_dir)
            
            # SQLite file
            sqlite_path = Path("sirca.db")
            results["filesystem"]["sqlite_exists"] = sqlite_path.exists()
            if sqlite_path.exists():
                results["filesystem"]["sqlite_size"] = f"{sqlite_path.stat().st_size / 1024:.2f} KB"
            
            # Media directory
            media_path = Path("app/core/resources/media")
            results["filesystem"]["media_dir_exists"] = media_path.exists()
            
            if media_path.exists():
                # Contar archivos de media
                pertenencias_dir = media_path / "pertenencias"
                vehiculos_dir = media_path / "vehiculos"
                
                results["filesystem"]["pertenencias_dir"] = {
                    "exists": pertenencias_dir.exists(),
                    "files": len(list(pertenencias_dir.rglob("*.*"))) if pertenencias_dir.exists() else 0
                }
                
                results["filesystem"]["vehiculos_dir"] = {
                    "exists": vehiculos_dir.exists(),
                    "files": len(list(vehiculos_dir.rglob("*.*"))) if vehiculos_dir.exists() else 0
                }
            
            # Espacio disponible (si es posible)
            try:
                import shutil
                total, used, free = shutil.disk_usage(current_dir)
                results["filesystem"]["disk_space"] = {
                    "total_gb": f"{total // (1024**3):.2f}",
                    "used_gb": f"{used // (1024**3):.2f}",
                    "free_gb": f"{free // (1024**3):.2f}"
                }
            except:
                pass
                
        except Exception as e:
            results["filesystem"]["error"] = f"❌ Error: {str(e)}"
        
        # === CONFIGURACIÓN ===
        results["config"] = {
            "app_name": settings.app_name,
            "debug": settings.debug,
            "database_url_type": "PostgreSQL" if "postgresql" in str(settings.database_url).lower() else "SQLite",
            "redis_configured": bool(settings.redis_url or settings.redis_host),
            "email_configured": bool(settings.email_host and settings.email_host_user)
        }
        
        return results
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"❌ Error en diagnóstico: {str(e)}",
                "traceback": traceback.format_exc()
            }
        )

@app.get("/diagnostics/redis")
async def diagnostics_redis():
    """Diagnóstico específico de Redis"""
    try:
        from app.modules.auth.blacklist import get_redis
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "environment_vars": {},
            "connection": {},
            "operations": {},
            "keys": {}
        }
        
        # Variables de entorno
        redis_vars = ["REDIS_URL", "REDIS_PRIVATE_URL", "REDIS_PUBLIC_URL", "REDIS_HOST", "REDIS_PORT"]
        for var in redis_vars:
            value = os.getenv(var)
            if value:
                # Ofuscar password para seguridad
                if "redis://" in value:
                    parts = value.split("@")
                    if len(parts) > 1:
                        results["environment_vars"][var] = f"{parts[0][:20]}...@{parts[1]}"
                    else:
                        results["environment_vars"][var] = value[:30] + "..."
                else:
                    results["environment_vars"][var] = value
            else:
                results["environment_vars"][var] = "Not set"
        
        # Test de conexión
        redis_client = get_redis()
        
        # Ping
        ping_result = redis_client.ping()
        results["connection"]["ping"] = f"✅ {ping_result}"
        
        # Info del servidor
        try:
            info = redis_client.info()
            results["connection"]["redis_version"] = info.get("redis_version", "Unknown")
            results["connection"]["uptime_seconds"] = info.get("uptime_in_seconds", 0)
            results["connection"]["connected_clients"] = info.get("connected_clients", 0)
            results["connection"]["memory_usage"] = f"{info.get('used_memory_human', 'Unknown')}"
        except Exception as e:
            results["connection"]["info_error"] = str(e)
        
        # Test de operaciones
        test_key = f"diagnostics:test:{datetime.now().timestamp()}"
        
        # Set
        redis_client.setex(test_key, 30, "test_value_123")
        results["operations"]["set"] = "✅ OK"
        
        # Get
        value = redis_client.get(test_key)
        results["operations"]["get"] = f"✅ OK: {value}"
        
        # Exists
        exists = redis_client.exists(test_key)
        results["operations"]["exists"] = f"✅ OK: {exists}"
        
        # Delete
        deleted = redis_client.delete(test_key)
        results["operations"]["delete"] = f"✅ OK: {deleted}"
        
        # Análisis de keys existentes
        all_keys = redis_client.keys("*")
        results["keys"]["total"] = len(all_keys)
        
        # Categorizar keys
        categories = {
            "blacklist": [k for k in all_keys if k.startswith("blacklist:")],
            "jwt_activacion": [k for k in all_keys if k.startswith("jwt:activacion:")],
            "jwt_reset": [k for k in all_keys if k.startswith("jwt:reset:")],
            "otros": [k for k in all_keys if not any(k.startswith(prefix) for prefix in ["blacklist:", "jwt:"])]
        }
        
        for category, keys in categories.items():
            results["keys"][category] = {
                "count": len(keys),
                "sample_keys": keys[:5] if keys else []  # Mostrar max 5 ejemplos
            }
        
        return results
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"❌ Error en diagnóstico Redis: {str(e)}",
                "traceback": traceback.format_exc()
            }
        )

@app.get("/diagnostics/database")
async def diagnostics_database():
    """Diagnóstico específico de base de datos"""
    try:
        from app.core.dependencias.dependencias import engine
        from sqlalchemy import text
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "config": {},
            "connection": {},
            "tables": {},
            "data": {}
        }
        
        # Configuración
        database_url = str(settings.database_url)
        results["config"]["url"] = database_url[:30] + "..." if len(database_url) > 30 else database_url
        results["config"]["type"] = "PostgreSQL" if "postgresql" in database_url.lower() else "SQLite"
        results["config"]["environment_var"] = os.getenv("DATABASE_URL", "Not set")[:30] + "..." if os.getenv("DATABASE_URL") else "Not set"
        
        with engine.connect() as conn:
            # Test de conexión
            test_result = conn.execute(text("SELECT 1 as test, 'connection_ok' as message")).fetchone()
            results["connection"]["status"] = "✅ Conectado"
            results["connection"]["test_query"] = f"✅ {test_result[0]} - {test_result[1]}"
            
            # Información del servidor
            try:
                if "postgresql" in database_url.lower():
                    version_result = conn.execute(text("SELECT version()")).fetchone()
                    results["connection"]["version"] = version_result[0][:100] + "..." if len(version_result[0]) > 100 else version_result[0]
                else:
                    version_result = conn.execute(text("SELECT sqlite_version()")).fetchone()
                    results["connection"]["version"] = f"SQLite {version_result[0]}"
            except Exception as e:
                results["connection"]["version_error"] = str(e)
            
            # Listar tablas
            try:
                if "postgresql" in database_url.lower():
                    tables_query = text("""
                        SELECT table_name, 
                               (SELECT COUNT(*) FROM information_schema.columns 
                                WHERE table_name = t.table_name AND table_schema = 'public') as column_count
                        FROM information_schema.tables t 
                        WHERE table_schema = 'public' 
                        ORDER BY table_name
                    """)
                else:
                    tables_query = text("""
                        SELECT name as table_name,
                               (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
                        FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """)
                
                tables_result = conn.execute(tables_query).fetchall()
                
                for table_name, column_count in tables_result:
                    try:
                        # Contar registros
                        count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                        results["tables"][table_name] = {
                            "columns": column_count,
                            "rows": count_result[0],
                            "status": "✅ OK"
                        }
                    except Exception as e:
                        results["tables"][table_name] = {
                            "columns": column_count,
                            "error": str(e)
                        }
                        
            except Exception as e:
                results["tables"]["error"] = str(e)
            
            # Datos de ejemplo (últimos registros)
            sample_queries = {
                "usuarios": "SELECT numero_documento, nombres, apellidos, activo FROM usuarios ORDER BY numero_documento DESC LIMIT 3",
                "pertenencias": "SELECT id, nombre, tipo, estado, usuario_id FROM pertenencias ORDER BY fecha_registro DESC LIMIT 3",
                "vehiculos": "SELECT placa, marca, modelo, estado, usuario_id FROM vehiculos ORDER BY fecha_registro DESC LIMIT 3"
            }
            
            for table, query in sample_queries.items():
                try:
                    sample_result = conn.execute(text(query)).fetchall()
                    results["data"][f"{table}_sample"] = [dict(row._mapping) for row in sample_result]
                except Exception as e:
                    results["data"][f"{table}_error"] = str(e)
        
        return results
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"❌ Error en diagnóstico de BD: {str(e)}",
                "traceback": traceback.format_exc()
            }
        )

@app.get("/diagnostics/files")
async def diagnostics_files():
    """Diagnóstico del sistema de archivos y media"""
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "directories": {},
            "files": {},
            "permissions": {}
        }
        
        # Directorio actual y estructura
        current_dir = Path.cwd()
        results["directories"]["current"] = str(current_dir)
        results["directories"]["exists"] = current_dir.exists()
        
        # Verificar estructura de directorios clave
        key_paths = {
            "app": Path("app"),
            "templates": Path("app/core/resources/templates"),
            "static": Path("app/core/resources/static"),
            "media": Path("app/core/resources/media"),
            "media_pertenencias": Path("app/core/resources/media/pertenencias"),
            "media_vehiculos": Path("app/core/resources/media/vehiculos")
        }
        
        for name, path in key_paths.items():
            try:
                results["directories"][name] = {
                    "path": str(path),
                    "exists": path.exists(),
                    "is_dir": path.is_dir() if path.exists() else False,
                    "files_count": len(list(path.rglob("*.*"))) if path.exists() else 0
                }
                
                if path.exists() and path.is_dir():
                    # Contar por tipo de archivo
                    all_files = list(path.rglob("*.*"))
                    extensions = {}
                    for file in all_files:
                        ext = file.suffix.lower()
                        extensions[ext] = extensions.get(ext, 0) + 1
                    results["directories"][name]["file_types"] = extensions
                    
            except Exception as e:
                results["directories"][name] = {"error": str(e)}
        
        # Archivos específicos importantes
        important_files = {
            "sqlite_db": Path("sirca.db"),
            "env_file": Path(".env"),
            "requirements": Path("requirements.txt"),
            "main_py": Path("app/main.py")
        }
        
        for name, file_path in important_files.items():
            try:
                if file_path.exists():
                    stat = file_path.stat()
                    results["files"][name] = {
                        "path": str(file_path),
                        "exists": True,
                        "size_bytes": stat.st_size,
                        "size_kb": f"{stat.st_size / 1024:.2f}",
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    }
                else:
                    results["files"][name] = {
                        "path": str(file_path),
                        "exists": False
                    }
            except Exception as e:
                results["files"][name] = {"error": str(e)}
        
        # Test de permisos de escritura
        test_dirs = [
            Path("app/core/resources/media"),
            Path("app/core/resources/media/pertenencias"),
            Path("app/core/resources/media/vehiculos")
        ]
        
        for test_dir in test_dirs:
            try:
                # Crear directorio si no existe
                test_dir.mkdir(parents=True, exist_ok=True)
                
                # Test de escritura
                test_file = test_dir / f"test_write_{datetime.now().timestamp()}.txt"
                test_file.write_text("test content")
                
                # Test de lectura
                content = test_file.read_text()
                
                # Limpiar
                test_file.unlink()
                
                results["permissions"][str(test_dir)] = {
                    "writable": True,
                    "readable": True,
                    "test": "✅ OK"
                }
                
            except Exception as e:
                results["permissions"][str(test_dir)] = {
                    "writable": False,
                    "error": str(e)
                }
        
        return results
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"❌ Error en diagnóstico de archivos: {str(e)}",
                "traceback": traceback.format_exc()
            }
        )

@app.get("/diagnostics/summary")
async def diagnostics_summary():
    """Resumen rápido del estado general"""
    try:
        summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "✅ OK",
            "issues": [],
            "components": {}
        }
        
        # Database
        try:
            from app.core.dependencias.dependencias import engine
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                summary["components"]["database"] = "✅ OK"
        except Exception as e:
            summary["components"]["database"] = f"❌ Error: {str(e)}"
            summary["issues"].append("Database connection failed")
            summary["overall_status"] = "⚠️ Issues detected"
        
        # Redis
        try:
            from app.modules.auth.blacklist import get_redis
            redis_client = get_redis()
            redis_client.ping()
            summary["components"]["redis"] = "✅ OK"
        except Exception as e:
            summary["components"]["redis"] = f"❌ Error: {str(e)}"
            summary["issues"].append("Redis connection failed")
            summary["overall_status"] = "⚠️ Issues detected"
        
        # File system
        media_path = Path("app/core/resources/media")
        if media_path.exists():
            summary["components"]["media_storage"] = "✅ OK"
        else:
            summary["components"]["media_storage"] = "⚠️ Media directory missing"
            summary["issues"].append("Media directory not found")
            summary["overall_status"] = "⚠️ Issues detected"
        
        # Environment
        summary["components"]["environment"] = "Railway" if os.getenv("RAILWAY_ENVIRONMENT") else "Local"
        summary["components"]["database_type"] = "PostgreSQL" if "postgresql" in str(settings.database_url).lower() else "SQLite"
        
        if not summary["issues"]:
            summary["overall_status"] = "✅ All systems operational"
        
        return summary
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"❌ Critical error: {str(e)}",
                "overall_status": "❌ Critical failure"
            }
        )