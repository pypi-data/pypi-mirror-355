from __future__ import annotations
from typing import Any, Dict, ClassVar, List, get_type_hints
from sqlalchemy import MetaData, Table as SQLAlchemyTable

from tai_sql import db
from .utils import (
    is_native_python_type,
    find_custom_type,
    get_relation_direction
)

from .base import DatabaseObject
from .relations import Relation, ForeignKey

class Table(DatabaseObject):
    """
    Clase para definir tablas de base de datos.
    Extiende DatabaseObject con funcionalidad específica para tablas.
    """
    
    __abstract__ = True
    __tablename__: ClassVar[str]
    __analized__: ClassVar[bool] = False
    
    # Específico de tablas
    relations: ClassVar[Dict[str, Relation]] = {}
    foreign_keys: ClassVar[List[ForeignKey]] = []
    
    def __init_subclass__(cls) -> None:
        """Inicialización específica para tablas"""
        super().__init_subclass__()
        
        # Inicializar atributos específicos de tabla
        cls.relations = {}
        cls.foreign_keys = []
        
        if not hasattr(cls, '__tablename__'):
            raise ValueError(f"La tabla {cls.__name__} debe definir __tablename__")

        cls.tablename = cls.__tablename__
        cls._name = cls.__tablename__  # Para compatibilidad con base
        cls.is_view = cls.__is_view__
    
    @classmethod
    def get_models(cls) -> List[Table]:
        """Retorna solo las tablas registradas"""
        return cls.get_registered_tables()

    @classmethod
    def get_ignored_attributes(cls) -> set:
        """Atributos específicos de tabla a ignorar"""
        return {'registry', 'columns', 'relations', 'foreign_keys', 'tablename'}
    
    @classmethod
    def analyze(cls) -> None:
        """Análisis completo para tablas (columnas + relaciones)"""
        if cls.__analized__:
            return
        
        for model in cls.registry:
            if not issubclass(model, Table):
                continue
                
            # Analizar columnas (método heredado)
            model.analyze_columns()
            
            # Analizar relaciones (específico de tablas)
            model.analyze_relations()
        
        # Procesar relaciones implícitas
        for model in cls.registry:
            if issubclass(model, Table):
                for implicit_relation in model.relations.values():
                    if implicit_relation.implicit:
                        implicit_relation.lazy_save()
        
        cls.validate()
        
        cls.__analized__ = True  # Marcar como analizado
    
    @classmethod
    def analyze_relations(cls) -> None:
        """Análisis específico de relaciones para tablas"""
        type_hints = get_type_hints(cls)
        
        for name, hint in type_hints.items():
            if name.startswith('__') or name in cls.get_ignored_attributes():
                continue
            
            value = getattr(cls, name, None)
            
            if isinstance(value, Relation):
                # Relación explícita
                relation = value
                relation.name = name
                relation.local = cls
                relation.target = find_custom_type(hint)
                relation.direction = get_relation_direction(hint)
                relation.columns.extend([col for name, col in cls.columns.items() if name in relation.fields])  # Asignar columna si existe
                relation.save()
            
            elif value is None and not is_native_python_type(hint):
                # Relación implícita
                relation = Relation(
                    name=name,
                    local=cls,
                    target=find_custom_type(hint),
                    direction=get_relation_direction(hint),
                    implicit=True
                )
                relation.store()
    
    @classmethod
    def validate(cls) -> None:
        """Validación específica para tablas"""
        for model in cls.registry:
            if not issubclass(model, Table):
                continue
            # Validar que tenga al menos una primary key
            if not any(col.primary_key for col in model.columns.values()):
                raise ValueError(f"La tabla {model._name} debe tener al menos una primary key")
    
    @classmethod
    def info(cls) -> Dict[str, Any]:
        """Información específica de tabla"""
        base_info = super().info()
        base_info.update({
            'tablename': cls.tablename,
            'relations': [rel.info() for rel in cls.relations.values()],
            'foreign_keys': [fk.info() for fk in cls.foreign_keys],
            'has_foreign_keys': len(cls.foreign_keys) > 0,
            'is_view': cls.is_view,
        })
        return base_info
    
    @classmethod
    def to_sqlalchemy_object(cls, metadata: MetaData):
        """Conversión a tabla SQLAlchemy"""
        return cls.to_sqlalchemy_table(metadata)
    
    @classmethod
    def to_sqlalchemy_table(cls, metadata: MetaData):
        """
        Convierte la definición de tai_sql a una tabla SQLAlchemy
        
        Args:
            metadata: MetaData de SQLAlchemy donde registrar la tabla
            
        Returns:
            Table: Tabla SQLAlchemy equivalente
        """
        
        # Convertir columnas
        cols = []
        for col in cls.columns.values():
            alchemy_col = col.to_sqlalchemy_column()
            cols.append(alchemy_col)
        
        # Convertir relaciones que sean foreign keys
        fks = []
        for fk in cls.foreign_keys:
            alchemy_fk = fk.to_sqlalchemy_foreign_key()
            fks.append(alchemy_fk)
        
        # Crear tabla SQLAlchemy
        table = SQLAlchemyTable(
            cls.tablename,
            metadata,
            *cols,
            *fks,
            schema=db.schema_name if db.provider.drivername == 'postgresql' else None,
        )
        
        return table
