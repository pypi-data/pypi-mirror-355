import sys
import click
from .commands.generate import GenerateCommand
from .commands.init import InitCommand, NewSchemaCommand
from .commands.push import PushCommand
from .commands.createdb import DBCommand
from .commands.utils import Connectivity, Schema

from tai_sql import db

@click.group()
def cli():
    """CLI para tai-sql: Un framework de ORM basado en SQLAlchemy."""
    pass

@cli.command()
@click.option('--name', '-n', default='database', help='Nombre del proyecto a crear')
@click.option('--schema-name', default='main', help='Nombre del primer esquema a crear')
def init(name: str, schema_name: str):
    """Inicializa un nuevo proyecto tai-sql"""
    command = InitCommand(namespace=name, schema_name=schema_name)
    try:
        command.check_poetry()
        command.check_directory_is_avaliable()
        command.check_virtualenv()
        command.create_project()
        command.add_dependencies()
        command.add_folders()
        command.view_example()
        command.msg()
    except Exception as e:
        click.echo(f"❌ Error al inicializar el proyecto: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--schema', '-s', help='Ruta al archivo de esquema (default=main)', default='database/schemas/main.py')
@click.option('--createdb', '-c', is_flag=True, help='Crea la base de datos si no existe')
@click.option('--force', '-f', is_flag=True, help='Forzar la generación de recursos, incluso si ya existen')
@click.option('--dry-run', '-d', is_flag=True, help='Mostrar las sentencias DDL sin ejecutarlas')
@click.option('--verbose', '-v', is_flag=True, help='Mostrar información detallada durante la ejecución')
def push(schema: str, createdb: bool, force: bool, dry_run: bool, verbose: bool):
    """Síncroniza el esquema con la base de datos"""

    db_command = DBCommand(schema)
    db_command.pre_validations()
    db_command.load_module()
    db_command.post_validations()
    db_command.warnings()
    command = PushCommand(schema)
    try:
        # Validar la configuración del schema
        

        click.echo(f"🚀 Push schema: {schema}")

        if createdb:
            # Crear la base de datos si no existe
            db_command.create()
        
        # Cargar y procesar el schema
        command.load_schema()

        # Validar nombres
        command.validate_schema_names()
        
        # Generar DDL
        ddl = command.generate()
        
        # Mostrar DDL
        if ddl:
            if verbose or dry_run:
                command.ddl_manager.show()
            else:
                click.echo("   ℹ️  Modo silencioso: No se mostrarán las sentencias DDL")
        
        if dry_run:
            click.echo("🔍 Modo dry-run: No se ejecutaron cambios")
            return
        
        # Confirmar ejecución
        if not force:
            confirm = click.confirm("¿Deseas ejecutar estas sentencias en la base de datos?")
            if not confirm:
                click.echo("❌ Operación cancelada")
                return
        
        # Ejecutar DDL
        changes = command.execute()

        if changes:
            generate = GenerateCommand(schema)

            try:
                click.echo()
                generate.run_generators()
                
            except Exception as e:
                click.echo(f"❌ Error inesperado: {str(e)}", err=True)
                sys.exit(1)
        
    except Exception as e:
        import logging
        logging.exception(e)
        click.echo(f"❌ Error al procesar schema: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--schema', '-s', help='Ruta al archivo de esquema (default=main)', default='database/schemas/main.py')
def generate(schema):
    """Genera recursos basados en los generadores configurados"""

    command = GenerateCommand(schema)

    try:
        command.pre_validations()
        command.load_module()
        command.post_validations()
        command.warnings()
        command.run_generators()
        
    except Exception as e:
        click.echo(f"❌ Error inesperado: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--project', default='database', help='Nombre del proyecto (default: database)')
@click.argument('name')
def new_schema(project: str, name: str):
    """Crea un nuevo esquema en el proyecto"""
    if not name:
        click.echo("❌ Error: Debes proporcionar un nombre para el esquema.", err=True)
        sys.exit(1)

    try:
        command = NewSchemaCommand(namespace=project, schema_name=name)
        command.create()
    except Exception as e:
        click.echo(f"❌ Error al crear el esquema: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--schema', '-s', help='Ruta al archivo de esquema (default=main)', default='database/schemas/main.py')
@click.option('--timeout', '-t', default=5, help='Timeout en segundos para la verificación (default: 5)')
@click.option('--check-db', '-d', is_flag=True, help='También verificar si la base de datos específica existe')
@click.option('--full', '-f', is_flag=True, help='Verificación completa (incluye ping ICMP, TCP y BD)')
@click.option('--quiet', '-q', is_flag=True, help='Modo silencioso, solo mostrar resultado final')
def ping(schema: str, timeout: int, check_db: bool, full: bool, quiet: bool):
    """Verifica la conectividad con el servidor"""
    
    # Cargar configuración del schema para obtener provider
    config = Schema(schema)
    try:
        config.pre_validations()
        config.load_module()
        config.post_validations()
    except Exception as e:
        click.echo(f"❌ Error al cargar configuración: {str(e)}", err=True)
        sys.exit(1)
    
    # Crear instancia de Connectivity
    connectivity = Connectivity()
    
    # Mostrar información de conexión si no está en modo silencioso
    if not quiet:

        click.echo("🔧 Información de conexión:")
        click.echo(f"   Motor: {db.provider.drivername}")
        click.echo(f"   Host: {db.provider.host}")
        click.echo(f"   Puerto: {db.provider.port}")
        click.echo(f"   Base de datos: {db.provider.database}")
        click.echo(f"   Usuario: {db.provider.username}")
        click.echo()
    
    success = True
    
    try:
        if full:
            # Verificación completa: ping + conectividad de BD
            if not quiet:
                click.echo("🌐 Verificación FULL")
                click.echo()
            
            if connectivity.verify(timeout):
                if not quiet:
                    click.echo()
                    click.echo("✅ Verificación de conectividad exitosa")
            else:
                if not quiet:
                    click.echo()
                    click.echo("❌ Falló la verificación de conectividad")
                success = False
        else:
            # Solo ping básico al host
            if not quiet:
                click.echo("🏓 Verificación BASIC")
                click.echo()
            
            if connectivity.ping_host(timeout):
                if not quiet:
                    click.echo()
                    click.echo("✅ Host accesible")
            else:
                if not quiet:
                    click.echo()
                    click.echo("❌ Host no accesible")
                success = False
        
        # Verificar existencia de la base de datos si se solicita
        if check_db and success:
            if not quiet:
                click.echo()
                click.echo("🗄️  Verificando existencia de la base de datos...")
            
            if connectivity.db_exist():
                if not quiet:
                    click.echo()
                    click.echo("✅ La base de datos existe")
            else:
                if not quiet:
                    click.echo()
                    click.echo("⚠️  La base de datos no existe")
                    click.echo("   💡 Sugerencia: Usa 'tai-sql push --createdb' para crearla")
                # No marcar como fallo si solo falta la BD
        
        # Resultado final
        if quiet:
            if success:
                click.echo("✅ CONECTIVIDAD OK")
            else:
                click.echo("❌ CONECTIVIDAD FALLIDA")
        else:
            click.echo()
            if success:
                click.echo("🎉 Verificación de conectividad completada exitosamente")
            else:
                click.echo("💥 Falló la verificación de conectividad")
        
        # Exit code apropiado
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        click.echo()
        click.echo("⚠️  Verificación interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        click.echo(f"❌ Error inesperado durante la verificación: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()