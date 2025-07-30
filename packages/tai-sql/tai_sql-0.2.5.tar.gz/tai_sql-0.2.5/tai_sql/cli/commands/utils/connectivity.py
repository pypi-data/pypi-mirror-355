import os
import socket
import subprocess
import platform
import click
from sqlalchemy import text, create_engine, URL
from sqlalchemy.exc import OperationalError, ProgrammingError

from tai_sql import db


class Connectivity:
    """
    Clase para manejar la conectividad a la base de datos.
    """


    def ping_host(self, timeout: int = 5) -> bool:
        """
        Verifica la conectividad al servidor de base de datos usando múltiples métodos.
        
        Args:
            timeout (int): Timeout en segundos para la verificación
            
        Returns:
            bool: True si el host está accesible, False en caso contrario
        """
        host = db.provider.host
        port = db.provider.port
        
        # Para SQLite no hay servidor remoto
        if db.provider.drivername == "sqlite":
            return True
        
        # Para localhost, usar métodos específicos
        if host in ['localhost', '127.0.0.1', '::1']:
            return self._ping_localhost(port, timeout)
        
        # Para hosts remotos, intentar múltiples métodos
        return self._ping_remote_host(host, port, timeout)
    
    def _ping_localhost(self, port: int, timeout: int) -> bool:
        """
        Verifica conectividad a localhost usando socket.
        
        Args:
            port (int): Puerto del servidor
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si localhost:port está accesible
        """
        click.echo(f"🔍 Verificando conectividad a localhost:{port}")
        
        try:
            with socket.create_connection(('localhost', port), timeout=timeout):
                click.echo(f"✅ localhost:{port} está accesible")
                return True
        except (socket.timeout, socket.error, ConnectionRefusedError) as e:
            click.echo(f"❌ localhost:{port} no está accesible: {e}")
            return False
    
    def _ping_remote_host(self, host: str, port: int, timeout: int) -> bool:
        """
        Verifica conectividad a un host remoto usando múltiples métodos.
        
        Args:
            host (str): Hostname o IP
            port (int): Puerto del servidor
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si el host está accesible
        """
        click.echo(f"🔍 Verificando conectividad a {host}:{port}")
        
        # Método 1: Verificar resolución DNS
        if not self._resolve_hostname(host):
            return False
        
        # Método 2: Ping ICMP (si está disponible)
        icmp_result = self._icmp_ping(host, timeout)
        
        # Método 3: Verificar conectividad TCP al puerto específico
        tcp_result = self._tcp_ping(host, port, timeout)
        
        # Mostrar resultados
        if icmp_result and tcp_result:
            click.echo()
            click.echo(f"✅ {host}:{port} está completamente accesible")
            return True
        elif tcp_result:
            click.echo()
            click.echo(f"✅ {host}:{port} está accesible (TCP), pero ICMP puede estar bloqueado")
            return True
        elif icmp_result:
            click.echo()
            click.echo(f"⚠️  {host} responde a ping, pero el puerto {port} no está accesible")
            return False
        else:
            click.echo()
            click.echo(f"❌ {host}:{port} no está accesible")
            return False
    
    def _resolve_hostname(self, host: str) -> bool:
        """
        Verifica que el hostname se pueda resolver a una IP.
        
        Args:
            host (str): Hostname a resolver
            
        Returns:
            bool: True si se puede resolver
        """
        try:
            ip = socket.gethostbyname(host)
            click.echo(f"   🔍 DNS: {host} → {ip}")
            return True
        except socket.gaierror as e:
            click.echo(f"   ❌ Error de DNS: No se puede resolver {host}: {e}")
            return False
    
    def _icmp_ping(self, host: str, timeout: int) -> bool:
        """
        Realiza un ping ICMP al host.
        
        Args:
            host (str): Host a hacer ping
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si el ping es exitoso
        """
        try:
            # Detectar sistema operativo para usar el comando correcto
            system = platform.system().lower()
            
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
            else:  # Linux, macOS, etc.
                cmd = ["ping", "-c", "1", "-W", str(timeout), host]
            
            # Ejecutar ping con timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 2  # Un poco más de timeout para el proceso
            )
            
            if result.returncode == 0:
                click.echo(f"   ✅ ICMP: {host} responde a ping")
                return True
            else:
                click.echo(f"   ⚠️  ICMP: {host} no responde a ping (puede estar bloqueado)")
                return False
                
        except subprocess.TimeoutExpired:
            click.echo(f"   ⚠️  ICMP: Timeout al hacer ping a {host}")
            return False
        except FileNotFoundError:
            click.echo(f"   ⚠️  ICMP: Comando ping no disponible")
            return False
        except Exception as e:
            click.echo(f"   ⚠️  ICMP: Error al hacer ping a {host}: {e}")
            return False
    
    def _tcp_ping(self, host: str, port: int, timeout: int) -> bool:
        """
        Verifica conectividad TCP al puerto específico.
        
        Args:
            host (str): Host a verificar
            port (int): Puerto a verificar
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si el puerto está accesible
        """
        try:
            with socket.create_connection((host, port), timeout=timeout):
                click.echo(f"   ✅ TCP: {host}:{port} está accesible")
                return True
        except (socket.timeout, socket.error, ConnectionRefusedError) as e:
            click.echo(f"   ❌ TCP: {host}:{port} no está accesible: {e}")
            return False
        except Exception as e:
            click.echo(f"   ❌ TCP: Error inesperado al conectar a {host}:{port}: {e}")
            return False
    
    def verify(self, timeout: int = 5) -> bool:
        """
        Verifica la conectividad completa al servidor de base de datos.
        
        Args:
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si hay conectividad completa
        """
        click.echo("🌐 Verificando conectividad al servidor de base de datos...")
        
        # Ping básico al host
        if not self.ping_host(timeout):
            click.echo("❌ No hay conectividad de red al servidor")
            return False
        
        # Intentar conexión a nivel de base de datos
        return self._test_db_connection(timeout)
    
    def _test_db_connection(self, timeout: int) -> bool:
        """
        Prueba la conectividad a nivel de base de datos (sin especificar una BD específica).
        
        Args:
            timeout (int): Timeout en segundos
            
        Returns:
            bool: True si se puede conectar al servidor de BD
        """
        try:
            click.echo()
            click.echo("🔍 Verificando conectividad del servidor de base de datos...")
            
            # Crear engine temporal sin especificar base de datos
            if db.provider.drivername == "postgresql":
                # Para PostgreSQL, conectar a la BD postgres (siempre existe)
                temp_url = URL.create(
                    drivername=db.provider.drivername,
                    username=db.provider.username,
                    password=db.provider.password,
                    host=db.provider.host,
                    port=db.provider.port,
                    database="postgres"
                )
            elif db.provider.drivername == "mysql":
                # Para MySQL, conectar sin especificar BD
                temp_url = URL.create(
                    drivername=db.provider.drivername,
                    username=db.provider.username,
                    password=db.provider.password,
                    host=db.provider.host,
                    port=db.provider.port
                )
            else:
                click.echo("✅ Conectividad verificada para SQLite")
                return True
            
            # Crear engine temporal con timeout
            temp_engine = create_engine(
                temp_url,
                connect_args={
                    "connect_timeout": timeout,
                    "options": f"-c statement_timeout={timeout * 1000}" if db.provider.drivername == "postgresql" else ""
                } if db.provider.drivername == "postgresql" else {
                    "connect_timeout": timeout
                }
            )
            
            # Probar conexión
            with temp_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
            click.echo("    ✅ Servidor de base de datos accesible y funcionando")
            return True
            
        except OperationalError as e:
            if "authentication" in str(e).lower() or "access denied" in str(e).lower():
                click.echo("⚠️  Servidor accesible pero hay problemas de autenticación")
                click.echo(f"   Verifica usuario/contraseña para {db.provider.username}")
                return True  # El servidor está ahí, solo falla auth
            else:
                click.echo(f"❌ Error de conexión al servidor: {e}")
                return False
        except Exception as e:
            click.echo(f"❌ Error inesperado al conectar al servidor: {e}")
            return False

    def db_exist(self) -> bool:
        """
        Verifica si existe la base de datos especificada en la configuración.
        
        Returns:
            bool: True si la base de datos existe, False en caso contrario
        """
        try:
            # Obtener la URL de conexión del engine
            
            click.echo(f"🔍 Verificando existencia de la base de datos: {db.provider.database}")
            
            with db.engine.connect() as conn:
                if db.provider.drivername == "postgresql":
                    # PostgreSQL
                    result = conn.execute(text(
                        "SELECT 1 FROM pg_database WHERE datname = :db_name"
                    ), {"db_name": db.provider.database})
                    
                elif db.provider.drivername == "mysql":
                    # MySQL/MariaDB
                    result = conn.execute(text(
                        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = :db_name"
                    ), {"db_name": db.provider.database})
                    
                elif db.provider.drivername == "sqlite":
                    # SQLite - verificar si el archivo existe
                    db_file = db.provider.database
                    exists = os.path.exists(db_file)
                    return exists
                    
                else:
                    click.echo(f"❌ Tipo de base de datos no implementado: {db.provider.drivername}", err=True)
                    return False
                
                exists = result.fetchone() is not None
                return exists
                
        except (OperationalError, ProgrammingError) as e:
            click.echo(f"❌ La base de datos no existe", err=True)
            return False
        except Exception as e:
            click.echo(f"❌ Error inesperado: {e}", err=True)
            return False