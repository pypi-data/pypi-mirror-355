from __future__ import annotations
import sys
import re
import click
from dataclasses import dataclass, field
from typing import List, Optional
from sqlalchemy import MetaData, Column, text, Engine
from sqlalchemy.schema import Table, UniqueConstraint

from tai_sql import db
from tai_sql.orm import Table, View
from .utils import Schema
from .utils.ddl import (
    DDLManager,
    CreateStatement,
    AlterColumnStatement,
    ForeignKeyStatement,
    CreateViewStatement,
    AlterViewStatement,
    DropViewStatement
)


@dataclass
class DriftManager:
    """
    Clase para almacenar los cambios detectados en el esquema (tablas y vistas)
    """
    engine: Engine = field(default_factory=lambda: db.engine)
    metadata: MetaData = field(default_factory=lambda: MetaData(db.schema_name if db.provider.drivername == 'postgresql' else None))
    existing_metadata: MetaData = field(default_factory=lambda: MetaData(db.schema_name if db.provider.drivername == 'postgresql' else None))
    
    # Tablas
    new_tables: dict[str, Table] = field(default_factory=dict)
    existing_tables: dict[str, Table] = field(default_factory=dict)
    columns_to_add: dict[str, list[Column]] = field(default_factory=dict)
    columns_to_drop: dict[str, list[Column]] = field(default_factory=dict)
    columns_to_modify: dict[str, list[Column]] = field(default_factory=dict)
    
    # Vistas
    new_views: dict[str, 'View'] = field(default_factory=dict)
    existing_views: dict[str, 'View'] = field(default_factory=dict)
    modified_views: dict[str, 'View'] = field(default_factory=dict)
    views_to_drop: dict[str, str] = field(default_factory=dict)  # view_name -> drop_statement

    debug_mode: bool = True  # Modo de depuración para mostrar detalles adicionales

    def detect(self) -> None:
        """
        Detecta cambios entre el esquema definido y el esquema actual
        
        Returns:
            dict: Diccionario con los cambios detectados
        """
        click.echo("🔎 Detectando cambios en el esquema...")

        self.table_changes()
        self.view_changes()


    def table_changes(self) -> None:
        """Detecta cambios en tablas"""

        self.existing_metadata.reflect(bind=self.engine)
        
        db_tables = set(self.existing_metadata.tables.keys())
        schema_tables = set(self.metadata.tables.keys())
        
        # Tablas nuevas
        new_tables = list(schema_tables - db_tables)

        for table_name in new_tables:
            new_table = self.metadata.tables[table_name]
            self.new_tables[table_name] = new_table
        
        # Tablas existentes
        existing_tables = list(schema_tables & db_tables)

        # Analizar cambios en columnas para tablas existentes
        for table_name in existing_tables:
            current_table = self.existing_metadata.tables[table_name]
            self.existing_tables[table_name] = current_table
            new_table = self.metadata.tables[table_name]

            constraint_columns = []
            # Check constrains
            for constraint in current_table.constraints:
                if isinstance(constraint, UniqueConstraint):
                    constraint_columns = [col.name for col in constraint.columns]
            
            current_columns = {col.name: col for col in current_table.columns}
            new_columns = {col.name: col for col in new_table.columns}
            
            # Columnas a añadir
            columns_to_add = set(new_columns.keys()) - set(current_columns.keys())
            if columns_to_add:
                self.columns_to_add[table_name] = [
                    new_columns[col_name] for col_name in columns_to_add
                ]
            
            # Columnas a eliminar (comentado por seguridad)
            columns_to_drop = set(current_columns.keys()) - set(new_columns.keys())
            if columns_to_drop:
                self.columns_to_drop[table_name] = [
                    current_columns[col_name] for col_name in columns_to_drop
                ]
            
            # Columnas a modificar
            for col_name in set(current_columns.keys()) & set(new_columns.keys()):
                current_col = current_columns[col_name]
                new_col = new_columns[col_name]

                type_mapper = {
                    'DATETIME': ['TIMESTAMP', 'TIMESTAMP WITH TIME ZONE'],
                    'INTEGER': ['INTEGER'],
                    'VARCHAR': ['VARCHAR', 'TEXT'],
                    'BIGINT': ['BIGINT', 'BIGSERIAL'],
                    'FLOAT': ['FLOAT', 'DOUBLE PRECISION'],
                }

                current_type = str(current_col.type)
                new_type = str(new_col.type)

                type_changed = current_type != new_type

                if (type_changed) and (new_type in type_mapper) and (current_type in type_mapper[new_type]):
                    type_changed = False

                # Comparar nullable
                nullable_changed = current_col.nullable != new_col.nullable
                
                # Comparar valor por defecto
                # default_changed = str(current_col.server_default) != str(new_col.server_default)
                
                # Comparar primary key
                pk_changed = current_col.primary_key != new_col.primary_key
                
                # Comparar autoincrement
                autoincrement_changed = current_col.autoincrement != new_col.autoincrement

                if col_name in constraint_columns:
                    current_col.unique = True

                # Comparar uniqueness
                unique_changed = current_col.unique != new_col.unique
                
                if type_changed or nullable_changed or pk_changed or autoincrement_changed or unique_changed:
                    if table_name not in self.columns_to_modify:
                        self.columns_to_modify[table_name] = []
                    self.columns_to_modify[table_name].append(new_col)

    # ✅ Actualizar el método view_changes para usar la comparación mejorada
    def view_changes(self) -> None:
        """Detecta cambios en vistas con comparación mejorada"""
        
        # Obtener vistas del registro
        schema_views = {view._name: view for view in View.get_models()}
        
        # Obtener vistas existentes en la base de datos
        existing_views = self.get_existing_views()
        
        # Vistas nuevas
        new_view_names = set(schema_views.keys()) - set(existing_views.keys())
        for view_name in new_view_names:
            self.new_views[view_name] = schema_views[view_name]
            click.echo(f"   🆕 Nueva vista detectada: {view_name}")
        
        # Vistas existentes - verificar si han cambiado
        # existing_view_names = set(schema_views.keys()) & set(existing_views.keys())
        # for view_name in existing_view_names:
        #     schema_view = schema_views[view_name]
        #     existing_view_query = existing_views[view_name]
            
        #     # ✅ Usar comparación semántica mejorada
        #     if not self._semantic_query_comparison(schema_view.query, existing_view_query):
        #         self.modified_views[view_name] = schema_view
        #         click.echo(f"   🔄 Vista modificada detectada: {view_name}")
        #     else:
        #         self.existing_views[view_name] = schema_view
        #         click.echo(f"   ✅ Vista sin cambios: {view_name}")
        
        # Vistas a eliminar (existen en BD pero no en schema)
        views_to_drop = set(existing_views.keys()) - set(schema_views.keys())

        for view_name in views_to_drop:
            drop_stmt = self._generate_drop_view_statement(view_name, existing_views[view_name])
            self.views_to_drop[view_name] = drop_stmt
            click.echo(f"   🗑️  Vista a eliminar: {view_name}")
    
    def get_existing_views(self) -> dict[str, str]:
        """
        Obtiene las vistas existentes en la base de datos con sus definiciones
        
        Returns:
            dict: {view_name: view_definition}
        """
        views = {}
        
        try:
            with self.engine.connect() as conn:
                if 'postgresql' in str(self.engine.dialect):
                    # PostgreSQL
                    result = conn.execute(text(f"""
                        SELECT 
                            table_name as view_name,
                            view_definition
                        FROM information_schema.views 
                        WHERE table_schema = COALESCE('{db.schema_name}', 'public')
                    """))
                    
                elif 'mysql' in str(self.engine.dialect):
                    # MySQL
                    result = conn.execute(text("""
                        SELECT 
                            TABLE_NAME as view_name,
                            VIEW_DEFINITION as view_definition
                        FROM information_schema.VIEWS
                        WHERE TABLE_SCHEMA = DATABASE()
                    """))
                    
                elif 'sqlite' in str(self.engine.dialect):
                    # SQLite
                    result = conn.execute(text("""
                        SELECT 
                            name as view_name,
                            sql as view_definition
                        FROM sqlite_master 
                        WHERE type = 'view'
                    """))
                    
                else:
                    click.echo("   ⚠️  Detección de vistas no soportada para este motor de BD")
                    return views
                
                for row in result:
                    views[row.view_name] = row.view_definition
                    
        except Exception as e:
            click.echo(f"   ⚠️  Error obteniendo vistas existentes: {e}")
        
        return views
    
    def _normalize_query(self, query: str) -> str:
        """
        Normaliza una consulta SQL para comparación robusta
        
        Args:
            query: Consulta SQL
            
        Returns:
            Consulta normalizada para comparación
        """
        
        if not query:
            return ""
        
        # Remover comentarios SQL
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Convertir a minúsculas para comparación insensible a mayúsculas
        query = query.lower()
        
        # Normalizar espacios en blanco (múltiples espacios, tabs, saltos de línea)
        query = re.sub(r'\s+', ' ', query)

        # Normalizar tipos de JOIN (INNER JOIN = JOIN)
        query = re.sub(r'\binner\s+join\b', 'join', query)
        query = re.sub(r'\bleft\s+outer\s+join\b', 'left join', query)
        query = re.sub(r'\bright\s+outer\s+join\b', 'right join', query)
        query = re.sub(r'\bfull\s+outer\s+join\b', 'full join', query)
        
        # Normalizar calificación de nombres de columnas
        # Esto maneja casos como "post.id" vs "id" cuando el contexto es claro
        query = self._normalize_column_qualification(query)
        
        # Normalizar alias en subconsultas
        # Remover alias innecesarios en funciones agregadas: "max(post.id) as max" -> "max(post.id)"
        # query = re.sub(r'(max|min|count|sum|avg)\s*\([^)]+\)\s+as\s+\w+', r'\1(\2)', query)
        
        # Normalizar paréntesis redundantes en WHERE y subconsultas
        query = self._normalize_parentheses(query)
        
        # Normalizar espacios alrededor de operadores y símbolos básicos
        query = re.sub(r'\s*([,;=<>!+\-*/])\s*', r'\1', query)
        
        # Normalizar espacios alrededor de AS
        query = re.sub(r'\s+as\s+', ' as ', query)
        
        # NUEVA MEJORA: Normalizar paréntesis alrededor de FROM clause
        # Esto maneja casos como "from(usuario left join post...)" -> "from usuario left join post..."
        query = re.sub(r'from\s*\(\s*([^)]+)\s*\)', r'from \1', query)
        
        # Normalizar JOIN syntax - remover paréntesis extra alrededor de condiciones JOIN
        # Esto maneja casos como "on((table1.id = table2.id))" -> "on table1.id = table2.id"
        query = re.sub(r'on\s*\(\s*\(\s*([^)]+)\s*\)\s*\)', r'on \1', query)
        query = re.sub(r'on\s*\(\s*([^)]+)\s*\)', r'on \1', query)
        
        # NUEVA MEJORA: Normalizar paréntesis redundantes en general
        # Remover paréntesis que no afectan la lógica (pero mantener los necesarios)
        query = re.sub(r'\(\s*([^()]*\s+(?:left|right|inner|outer|full)?\s*join\s+[^()]*)\s*\)', r'\1', query)
        
        # Normalizar espacios alrededor de palabras clave JOIN
        query = re.sub(r'\s+(left|right|inner|outer|full)\s+join\s+', r' \1 join ', query)
        query = re.sub(r'\s+join\s+', ' join ', query)
        
        # Normalizar GROUP BY y ORDER BY
        query = re.sub(r'\s+group\s+by\s+', ' group by ', query)
        query = re.sub(r'\s+order\s+by\s+', ' order by ', query)
        
        # Normalizar WHERE
        query = re.sub(r'\s+where\s+', ' where ', query)
        
        # Normalizar SELECT y FROM
        query = re.sub(r'\s+from\s+', ' from ', query)
        query = re.sub(r'^\s*select\s+', 'select ', query)
        
        # Normalizar funciones como COUNT, SUM, etc.
        query = re.sub(r'([a-z_]+)\s*\(\s*([^)]*)\s*\)', r'\1(\2)', query)
        
        # ✅ NUEVA MEJORA: Normalizar espacios alrededor de paréntesis restantes
        query = re.sub(r'\s*\(\s*', '(', query)
        query = re.sub(r'\s*\)\s*', ')', query)
        
        # Remover espacios extra al inicio y final
        query = query.strip()
        
        # Remover punto y coma final si existe
        query = query.rstrip(';')
        
        return query

    def _normalize_column_qualification(self, query: str) -> str:
        """
        Normaliza la calificación de nombres de columnas para hacer comparaciones más flexibles
        
        Args:
            query: Consulta SQL
            
        Returns:
            Consulta con calificación de columnas normalizada
        """
        
        # Extraer alias de tablas del FROM y JOIN
        table_aliases = {}
        
        # Buscar alias en FROM clause
        from_match = re.search(r'from\s+(\w+)\s+(\w+)(?:\s|$)', query)
        if from_match:
            table_aliases[from_match.group(2)] = from_match.group(1)
        
        # Buscar alias en JOINs
        join_matches = re.finditer(r'join\s+(\w+)\s+(\w+)\s+on', query)
        for match in join_matches:
            table_aliases[match.group(2)] = match.group(1)
        
        # Para cada alias, intentar normalizar las referencias
        for alias, table in table_aliases.items():
            # Reemplazar alias.column con table.column cuando sea posible
            # Pero solo si no causa ambigüedad
            pattern = rf'\b{re.escape(alias)}\.(\w+)'
            query = re.sub(pattern, rf'{table}.\1', query)
        
        return query

    def _normalize_parentheses(self, query: str) -> str:
        """
        Normaliza paréntesis redundantes en consultas SQL
        
        Args:
            query: Consulta SQL
            
        Returns:
            Consulta con paréntesis normalizados
        """
        
        # ✅ Remover paréntesis redundantes alrededor de subconsultas en WHERE
        # "where(p.id=(select...))" -> "where p.id=(select...)"
        query = re.sub(r'where\s*\(\s*([^()]*=\([^)]+\))\s*\)', r'where \1', query)
        
        # ✅ Remover paréntesis redundantes alrededor de condiciones WHERE simples
        # "where(table.column=value)" -> "where table.column=value"
        query = re.sub(r'where\s*\(\s*([^()]+)\s*\)(?!\s*(?:and|or))', r'where \1', query)
        
        # ✅ Normalizar paréntesis en subconsultas SELECT
        # "(select max(post.id) as max from...)" -> "(select max(post.id) from...)"
        query = re.sub(r'\(select\s+([^)]+)\s+as\s+\w+\s+from', r'(select \1 from', query)
        
        # ✅ Remover paréntesis dobles redundantes
        # "((condition))" -> "condition"
        while re.search(r'\(\s*\([^()]+\)\s*\)', query):
            query = re.sub(r'\(\s*\(([^()]+)\)\s*\)', r'(\1)', query)
        
        return query

    def _enhanced_query_normalization(self, query: str) -> str:
        """
        Normalización mejorada específica para PostgreSQL y otros motores
        
        Args:
            query: Consulta SQL original
            
        Returns:
            Consulta normalizada con reglas específicas del motor
        """
        
        # Aplicar normalización básica primero
        normalized = self._normalize_query(query)
        
        # ✅ Reglas específicas para PostgreSQL
        if 'postgresql' in str(self.engine.dialect):
            # PostgreSQL tiende a añadir paréntesis extra en FROM clauses con JOINs
            # "from(table1 left join table2 on condition)" -> "from table1 left join table2 on condition"
            normalized = re.sub(r'from\s*\(\s*([^)]+(?:join[^)]*)*)\s*\)', r'from \1', normalized)
            
            # PostgreSQL reformatea condiciones ON con paréntesis dobles
            # "on((condition))" -> "on condition"
            normalized = re.sub(r'on\s*\(\s*\(\s*([^)]+)\s*\)\s*\)', r'on \1', normalized)
            
        # ✅ Reglas específicas para MySQL
        elif 'mysql' in str(self.engine.dialect):
            # MySQL maneja backticks en nombres
            normalized = re.sub(r'`([^`]+)`', r'\1', normalized)
            
        # ✅ Reglas específicas para SQLite
        elif 'sqlite' in str(self.engine.dialect):
            # SQLite maneja comillas dobles en nombres
            normalized = re.sub(r'"([^"]+)"', r'\1', normalized)
        
        # ✅ Normalización final: remover espacios redundantes
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _semantic_query_comparison(self, query1: str, query2: str) -> bool:
        """
        Comparación semántica mejorada de consultas SQL
        
        Args:
            query1: Primera consulta
            query2: Segunda consulta
            
        Returns:
            bool: True si las consultas son semánticamente equivalentes
        """
        # 1. Normalización básica
        norm1 = self._normalize_query(query1)
        norm2 = self._normalize_query(query2)
        
        if norm1 == norm2:
            return True
        
        # 2. Normalización mejorada específica del motor
        enhanced1 = self._enhanced_query_normalization(query1)
        enhanced2 = self._enhanced_query_normalization(query2)
        
        if enhanced1 == enhanced2:
            return True
        
        # 3. Normalización avanzada con sqlparse si está disponible
        try:
            adv_norm1 = self._advanced_normalize_query(query1)
            adv_norm2 = self._advanced_normalize_query(query2)
            
            if adv_norm1 == adv_norm2:
                return True
        except:
            pass
        
        # 4. Comparación por componentes estructurales
        components_match = self._compare_query_components(enhanced1, enhanced2)
        
        # 5. ✅ Debug mejorado si las consultas siguen siendo diferentes
        if not components_match and hasattr(self, 'debug_mode') and self.debug_mode:
            click.echo(f"      🔍 Análisis detallado:")
            click.echo(f"         Básica 1: '{norm1}'")
            click.echo(f"         Básica 2: '{norm2}'")
            click.echo(f"         Mejorada 1: '{enhanced1}'")
            click.echo(f"         Mejorada 2: '{enhanced2}'")
            
            # Mostrar diferencias específicas
            differences = self._find_query_differences(enhanced1, enhanced2)
            if differences:
                click.echo(f"         Diferencias: {differences}")
        
        return components_match

    def _advanced_normalize_query(self, query: str) -> str:
        """
        Normalización avanzada que parsea la estructura SQL
        
        Args:
            query: Consulta SQL original
            
        Returns:
            Consulta normalizada estructuralmente
        """
        try:
            # Intentar usar sqlparse si está disponible para normalización más robusta
            import sqlparse
            
            # Parsear la consulta
            parsed = sqlparse.parse(query)[0]
            
            # Formatear con configuración consistente
            formatted = sqlparse.format(
                str(parsed),
                reindent=False,
                strip_comments=True,
                keyword_case='lower',
                identifier_case='lower',
                strip_whitespace=True
            )
            
            # Aplicar normalización adicional
            return self._normalize_query(formatted)
            
        except ImportError:
            # sqlparse no disponible, usar normalización básica
            return self._normalize_query(query)
        except Exception:
            # Error en parsing, fallback a normalización básica
            return self._normalize_query(query)


    def _compare_query_components(self, query1: str, query2: str) -> bool:
        """
        Compara componentes estructurales de las consultas
        
        Args:
            query1: Primera consulta normalizada
            query2: Segunda consulta normalizada
            
        Returns:
            bool: True si los componentes principales coinciden
        """
        
        def extract_components(query):
            components = {}
            
            # Extraer SELECT
            select_match = re.search(r'select\s+(.+?)\s+from', query, re.IGNORECASE | re.DOTALL)
            components['select'] = select_match.group(1).strip() if select_match else ""
            
            # Extraer FROM
            from_match = re.search(r'from\s+(.+?)(?:\s+where|\s+group|\s+order|\s+limit|$)', query, re.IGNORECASE)
            components['from'] = from_match.group(1).strip() if from_match else ""
            
            # Extraer WHERE
            where_match = re.search(r'where\s+(.+?)(?:\s+group|\s+order|\s+limit|$)', query, re.IGNORECASE)
            components['where'] = where_match.group(1).strip() if where_match else ""
            
            # Extraer GROUP BY
            group_match = re.search(r'group\s+by\s+(.+?)(?:\s+order|\s+limit|$)', query, re.IGNORECASE)
            components['group_by'] = group_match.group(1).strip() if group_match else ""
            
            # Extraer ORDER BY
            order_match = re.search(r'order\s+by\s+(.+?)(?:\s+limit|$)', query, re.IGNORECASE)
            components['order_by'] = order_match.group(1).strip() if order_match else ""
            
            return components
        
        comp1 = extract_components(query1)
        comp2 = extract_components(query2)
        
        # Comparar cada componente
        for key in comp1:
            # Normalizar componentes individuales
            norm_comp1 = re.sub(r'\s+', ' ', comp1[key]).strip()
            norm_comp2 = re.sub(r'\s+', ' ', comp2[key]).strip()
            
            if norm_comp1 != norm_comp2:
                return False
        
        return True

    def _find_query_differences(self, query1: str, query2: str) -> list[str]:
        """
        Encuentra las diferencias específicas entre dos consultas
        
        Args:
            query1: Primera consulta
            query2: Segunda consulta
            
        Returns:
            Lista de diferencias encontradas
        """
        differences = []
        
        # Comparar longitud
        if len(query1) != len(query2):
            differences.append(f"Longitud diferente ({len(query1)} vs {len(query2)})")
        
        # Encontrar posición de primera diferencia
        for i, (c1, c2) in enumerate(zip(query1, query2)):
            if c1 != c2:
                start = max(0, i - 10)
                end = min(len(query1), i + 10)
                context1 = query1[start:end].replace(c1, f"[{c1}]", 1)
                context2 = query2[start:end].replace(c2, f"[{c2}]", 1)
                differences.append(f"Pos {i}: '{context1}' vs '{context2}'")
                break
        
        return differences

    # ✅ Método de testing para validar normalización
    def test_query_normalization(self):
        """Método para probar la normalización con casos conocidos"""
        test_cases = [
            (
                "select usuario.id as user_id,usuario.name as user_name,count(post.id)as post_count from usuario left join post on usuario.id=post.author_id group by usuario.id,usuario.name",
                "select usuario.id as user_id,usuario.name as user_name,count(post.id)as post_count from(usuario left join post on usuario.id=post.author_id)group by usuario.id,usuario.name"
            ),
            (
                "SELECT t1.id, t2.name FROM table1 t1 LEFT JOIN table2 t2 ON t1.id = t2.id",
                "select t1.id,t2.name from(table1 t1 left join table2 t2 on((t1.id = t2.id)))"
            )
        ]
        
        click.echo("🧪 Probando normalización de consultas:")
        for i, (q1, q2) in enumerate(test_cases, 1):
            result = self._semantic_query_comparison(q1, q2)
            status = "✅" if result else "❌"
            click.echo(f"   Test {i}: {status}")
            if not result:
                click.echo(f"      Q1: {self._enhanced_query_normalization(q1)}")
                click.echo(f"      Q2: {self._enhanced_query_normalization(q2)}")

    def _generate_drop_view_statement(self, view_name: str, view_definition: str) -> str:
        """
        Genera statement DROP VIEW
        
        Args:
            view_name: Nombre de la vista
            view_definition: Definición de la vista
            
        Returns:
            Statement DROP VIEW
        """
        # Detectar si es vista materializada
        is_materialized = 'materialized' in view_definition.lower()
        view_type = "MATERIALIZED VIEW" if is_materialized else "VIEW"
        
        return f"DROP {view_type} IF EXISTS {view_name}"

    def show(self):
        """Muestra un resumen de los cambios detectados"""
        click.echo("📋 Resumen de cambios:")
        
        if self.new_tables:
            click.echo(f"   🆕 {len(self.new_tables)} tabla(s) nueva(s): {', '.join(self.new_tables)}")
        
        if self.columns_to_add:
            total_columns = sum(len(cols) for cols in self.columns_to_add.values())
            click.echo(f"   ➕ {total_columns} columna(s) a añadir en {len(self.columns_to_add)} tabla(s)")
        
        if self.columns_to_drop:
            total_columns = sum(len(cols) for cols in self.columns_to_drop.values())
            click.echo(f"   ⚠️  {total_columns} columna(s) serían eliminadas")
        
        if self.columns_to_modify:
            total_columns = sum(len(cols) for cols in self.columns_to_modify.values())
            click.echo(f"   ✏️  {total_columns} columna(s) a modificar en {len(self.columns_to_modify)} tabla(s)")
        
        if self.new_views:
            click.echo(f"   🆕 {len(self.new_views)} vista(s) nueva(s): {', '.join(self.new_views)}")
        
        if self.modified_views:
            click.echo(f"   🔄 {len(self.modified_views)} vista(s) modificada(s): {', '.join(self.modified_views)}")
        
        if self.views_to_drop:
            click.echo(f"   🗑️  {len(self.views_to_drop)} vista(s) a eliminar: {', '.join(self.views_to_drop)}")

        # Verificar si no hay cambios
        has_table_changes = self.new_tables or self.columns_to_add or self.columns_to_drop or self.columns_to_modify
        has_view_changes = self.new_views or self.modified_views or self.views_to_drop
        
        if not has_table_changes and not has_view_changes:
            click.echo("   ✅ No se detectaron cambios")
        
        click.echo()

class PushCommand(Schema):
    """
    Comando para generar y ejecutar sentencias DDL CREATE TABLE basadas en un schema.
    
    Este comando procesa un archivo de schema, genera las sentencias DDL necesarias
    para crear las tablas definidas y las ejecuta en la base de datos configurada.
    """

    def __init__(self, schema_file: str):
        super().__init__(schema_file)
        self.schema_file = schema_file
        self.ddl_manager = DDLManager()
        self.drift_manager = DriftManager()

    def load_schema(self) -> MetaData:
        """
        Carga y ejecuta el archivo de schema para obtener las definiciones de tablas
        
        Returns:
            MetaData: Metadata de SQLAlchemy con las tablas definidas
        """
        click.echo("📖 Cargando definiciones de schema...")
        
        try:
            # Limpiar estado previo
            db.tables = []
            db.views = []

            Table.analyze()
            View.analyze()

            db.tables = Table.get_models()
            db.views = View.get_models()

            for table in db.tables:
                # Convertir la definición de tai_sql a tabla SQLAlchemy
                sqlalchemy_table = table.to_sqlalchemy_table(self.drift_manager.metadata)
                click.echo(f"   📋 Tabla: {sqlalchemy_table.name}")
            
            for view in db.views:
                click.echo(f"   👁️  Vista: {view._name}")

            return self.drift_manager.metadata
            
        except Exception as e:
            raise Exception(f"Error al cargar schema: {e}")
    
    def validate_schema_names(self):
        """
        Valida que los nombres de tablas y columnas no sean palabras reservadas
        """
        click.echo("🔍 Validando nombres de tablas y columnas...")
        
        warnings = []
        
        for table in self.drift_manager.metadata.tables.values():
            # Validar nombre de tabla
            if table.name.lower() in self.ddl_manager.ddl.reserved_words:
                warnings.append(f"⚠️  Tabla '{table.name}' es una palabra reservada")
            
            # Validar nombres de columnas
            for column in table.columns:
                if column.name.lower() in self.ddl_manager.ddl.reserved_words:
                    warnings.append(f"⚠️  Columna '{column.name}' en tabla '{table.name}' es una palabra reservada")
        
        if warnings:
            click.echo("❌ Se encontraron problemas con nombres:")
            for warning in warnings:
                click.echo(f"   {warning}")
            click.echo()
            click.echo("💡 Sugerencias:")
            click.echo("   - Cambia 'user' por 'users' o 'app_user'")
            click.echo("   - Cambia 'order' por 'orders' o 'user_order'")
            click.echo("   - Usa nombres descriptivos que no sean palabras reservadas")
            click.echo()
            
            if not click.confirm("¿Continuar de todas formas? (se manejará automáticamente)"):
                click.echo("❌ Operación cancelada por el usuario")
                sys.exit(1)
        
        click.echo("✅ Validación de nombres completada")
    
    def generate(self) -> None:
        """
        Genera las sentencias DDL considerando cambios incrementales
        
        Returns:
            Lista de sentencias DDL como strings
        """

        # Limpiar sentencias previas
        self.ddl_manager.clear()
        # Detectar cambios
        self.drift_manager.detect()
        
        # Mostrar resumen de cambios
        self.drift_manager.show()

        new_tables = self.drift_manager.new_tables
        new_cols = self.drift_manager.columns_to_add
        delete_cols = self.drift_manager.columns_to_drop
        modify_cols = self.drift_manager.columns_to_modify

        if new_tables:
            self.ddl_manager.generate_creations(new_tables.values())
        
        # Generar migraciones para tablas existentes
        if new_cols or delete_cols or modify_cols:
            self.ddl_manager.generate_migrations(new_cols, delete_cols, modify_cols)
        
        new_views = self.drift_manager.new_views
        modified_views = self.drift_manager.modified_views
        views_to_drop = self.drift_manager.views_to_drop

        if views_to_drop:
            self.ddl_manager.generate_view_drops(views_to_drop)
        
        if new_views:
            self.ddl_manager.generate_view_creations(new_views)
        
        if modified_views:
            self.ddl_manager.generate_view_modifications(modified_views)

        return self.ddl_manager.statements
    
    def execute(self) -> Optional[int]:
        """Ejecuta las sentencias DDL en la base de datos"""
        if not self.ddl_manager.statements:
            click.echo("ℹ️  No hay cambios para aplicar")
            return
            
        click.echo("⚙️  Ejecutando sentencias DDL...")
        
        try:
            executed_count = 0
            
            with self.drift_manager.engine.connect() as conn:
                # Usar transacción para todas las operaciones
                trans = conn.begin()
                
                try:
                    for stmt in self.ddl_manager.statements:

                        if isinstance(stmt, CreateStatement):
                            # Ejecutar CREATE TABLE
                            conn.execute(text(stmt.text))
                            executed_count += 1
                            click.echo(f"   ⚙️  Crear tabla → {stmt.table_name}")
                            
                        elif isinstance(stmt, AlterColumnStatement):
                            # Ejecutar ALTER TABLE

                            if stmt.column.unique:
                                result = stmt.check_unique_constraints()

                                if result:
                                    click.echo("   ❌  UniqueConstraint error:")
                                    click.echo(f'   ⚠️  Columna "{stmt.column_name}" tiene valores duplicados en {stmt.table_name}, se omitirá la modificación')
                                    continue

                            if isinstance(stmt.text, List):
                                for sub_stmt in stmt.text:
                                    conn.execute(text(sub_stmt))
                            else:

                                conn.execute(text(stmt.text))

                            executed_count += 1

                            if stmt.column_name:
                                click.echo(f"   ⚙️ Añadir/modificar columna → {stmt.column_name} en {stmt.table_name}")

                        elif isinstance(stmt, ForeignKeyStatement):

                            # Ejecutar ALTER TABLE
                            conn.execute(text(stmt.text))
                            executed_count += 1

                            # Mostrar información de la ForeignKey
                            local_columns_names = [col.name for col in stmt.fk.columns]
                            target_columns_names = [element.column.name for element in stmt.fk.elements]
                            # Asegurar el mismo orden
                            local_columns_names.sort()
                            target_columns_names.sort()

                            click.echo(f'   ⚙️  Declarar ForeignKey: {stmt.local.name}[{", ".join(local_columns_names)}] → {stmt.target.name}[{", ".join(target_columns_names)}] en {stmt.local.name}')
                        
                        elif isinstance(stmt, CreateViewStatement):
                            conn.execute(text(stmt.text))
                            executed_count += 1
                            click.echo(f"   ⚙️  Crear vista → {stmt.view_name}")
                            
                        elif isinstance(stmt, AlterViewStatement):
                            conn.execute(text(stmt.text))
                            executed_count += 1
                            click.echo(f"   ⚙️  Modificar vista → {stmt.view_name}")
                            
                        elif isinstance(stmt, DropViewStatement):
                            conn.execute(text(stmt.text))
                            executed_count += 1
                            click.echo(f"   ⚙️  Eliminar vista → {stmt.view_name}")
                    
                    trans.commit()
                    click.echo(f"   🎉 {executed_count} operación(es) ejecutada(s) exitosamente")

                    return executed_count
                    
                except Exception as e:
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            raise Exception(f"Error al ejecutar DDL: {e}")
    