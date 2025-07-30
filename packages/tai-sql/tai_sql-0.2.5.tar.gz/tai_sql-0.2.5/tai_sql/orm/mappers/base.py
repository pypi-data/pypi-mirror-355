from __future__ import annotations
from typing import Any, Dict, ClassVar, List, get_type_hints, TYPE_CHECKING
from abc import ABC, abstractmethod
from sqlalchemy import MetaData

from .columns import Column
from .utils import (
    is_native_python_type,
    is_optional,
    mapped_type
)

if TYPE_CHECKING:
    from .table import Table  # Evitar circular imports
    from .view import View    # Evitar circular imports



class DatabaseObject(ABC):
    """
    Clase base abstracta para objetos de base de datos (Tables y Views).
    
    Proporciona funcionalidad común para análisis de type hints,
    manejo de columnas y conversión a SQLAlchemy.
    """
    
    __abstract__ = True
    __name__: ClassVar[str]  # Nombre del objeto (tabla o vista)
    __is_view__: ClassVar[bool] = False  # Indica si es una vista
    __description__: ClassVar[str] = ""  # Descripción opcional del objeto
    # Registro centralizado de todos los objetos de BD
    registry: ClassVar[List[DatabaseObject]] = []
    
    # Columnas comunes a tablas y vistas
    columns: ClassVar[Dict[str, Column]] = {}
    
    def __init_subclass__(cls) -> None:
        """Inicialización común para subclases"""
        super().__init_subclass__()
        
        # Inicializar diccionarios para esta clase específica
        cls.columns = {}
        
        if not hasattr(cls, '__name__'):
            raise ValueError(f"El objeto {cls.__name__} debe definir un atributo __name__")
        
        cls._name = cls.__name__
        cls._description = cls.__description__

        if cls._name in 'Base':
            raise ValueError(f"El objeto {cls.__name__} no puede llamarse 'Base'")
        
        # Solo añadir al registro si no es una clase abstracta
        if cls._should_register():
            DatabaseObject.registry.append(cls)

    @classmethod
    def _should_register(cls) -> bool:
        """
        Determina si la clase debe ser registrada.
        
        Returns:
            bool: True si debe registrarse, False si es una clase base o abstracta
        """
        # Clases que nunca deben registrarse (clases base del framework)
        framework_classes = {
            'DatabaseObject',
            'Table', 
            'View'
        }
        
        # No registrar clases del framework
        if cls.__name__ in framework_classes:
            return False
        
        # Si llegamos aquí, es una clase concreta que debe registrarse
        return True
    
    @classmethod
    def analyze_columns(cls) -> None:
        """
        Analiza los type hints de la clase para descubrir columnas.
        Método común para Tables y Views.
        """
        type_hints = get_type_hints(cls)
        
        for name, hint in type_hints.items():
            # Ignorar atributos especiales y de clase
            if name.startswith('__') or name.startswith('_') or name in cls.get_ignored_attributes():
                continue
            
            value = getattr(cls, name, None)
            mappedtype = mapped_type(hint)
            
            # Procesar como columna
            if isinstance(value, Column):
                # Ya es una Column (definida con column())
                column = value
                column.name = name
                column.type = mappedtype
                column.model = cls
                column.nullable = is_optional(hint)
                column.save()
            
            elif value is None and is_native_python_type(hint):
                # Columna implícita
                column = Column(
                    name=name,
                    type=mappedtype,
                    model=cls,
                    nullable=is_optional(hint)
                )
                column.save()
            
            elif value is not None and is_native_python_type(hint) and not cls.__is_view__:
                # Columna con valor por defecto
                if mappedtype != mapped_type(type(value)):
                    raise TypeError(
                        f"El tipo del valor por defecto [{value}] no coincide "
                        f"con el tipo esperado '{mappedtype}' para '{name}' en '{cls.__name__}'"
                    )
                
                column = Column(
                    name=name,
                    type=mappedtype,
                    model=cls,
                    default=value,
                    nullable=is_optional(hint)
                )
                column.save()
    
    @classmethod
    @abstractmethod
    def get_ignored_attributes(cls) -> set:
        """Retorna los atributos que deben ser ignorados durante el análisis"""
        pass
    
    @classmethod
    def info(cls) -> Dict[str, Any]:
        """Información básica común"""
        return {
            'name': cls.__name__,
            'object_name': cls._name,
            'columns': [col.info() for col in cls.columns.values()]
        }
    
    @classmethod
    @abstractmethod
    def validate(cls) -> None:
        """Validación específica del tipo de objeto"""
        pass
    
    @classmethod
    @abstractmethod
    def to_sqlalchemy_object(cls, metadata: MetaData):
        """Conversión a objeto SQLAlchemy"""
        pass

    @classmethod
    def get_registered_tables(cls) -> List[Table]:
        """Retorna solo las tablas registradas"""
        from .table import Table  # Import local para evitar circular imports
        return [obj for obj in cls.registry if isinstance(obj, type) and issubclass(obj, Table)]
    
    @classmethod
    def get_registered_views(cls) -> List[View]:
        """Retorna solo las vistas registradas"""
        from .view import View  # Import local para evitar circular imports
        return [obj for obj in cls.registry if isinstance(obj, type) and issubclass(obj, View)]
    
    @classmethod
    def debug_registry(cls) -> None:
        """Método de debug para ver qué está registrado"""
        print(f"Total objetos registrados: {len(cls.registry)}")
        for obj in cls.registry:
            obj_type = "Table" if not obj.__is_view__ else "View"
            print(f"  - {obj.__name__} ({obj_type})")