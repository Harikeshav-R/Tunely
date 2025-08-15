from pathlib import Path
from typing import Any, Dict, Type
from sqlalchemy import Column, Integer, create_engine
from sqlalchemy.orm import declarative_base, Session

from tunely.utils.constants import Constants
from tunely.utils.logger import Logger

Base = declarative_base()


class ConfigManager:
    _engine = None
    _models: Dict[str, Type[Base]] = {}

    @staticmethod
    def init(config_file_path: Path = Constants.CONFIG_PATH) -> None:
        ConfigManager._engine = create_engine(f"sqlite:///{config_file_path}")
        Base.metadata.create_all(ConfigManager._engine)
        Logger.debug("Config database initialized.")
        Logger.debug(f"Database path: {Constants.CONFIG_PATH}")

    @staticmethod
    def create_section(section_name: str, fields: Dict[str, type], defaults: Dict[str, Any] = None) -> None:
        attrs = {"__tablename__": section_name.lower(), "id": Column(Integer, primary_key=True)}
        for field_name, field_type in fields.items():
            attrs[field_name] = Column(field_type)
        model = type(section_name, (Base,), attrs)
        ConfigManager._models[section_name] = model
        Base.metadata.create_all(ConfigManager._engine)
        if defaults:
            ConfigManager.set_section_defaults(section_name, defaults)

    @staticmethod
    def set_section_defaults(section_name: str, defaults: Dict[str, Any]) -> None:
        """Initialize section with default values if missing."""
        model = ConfigManager._models[section_name]
        with Session(ConfigManager._engine) as session:
            row = session.query(model).first()
            if row is None:
                session.add(model(**defaults))
            else:
                for key, value in defaults.items():
                    if not hasattr(row, key) or getattr(row, key) is None:
                        setattr(row, key, value)
            session.commit()

    @staticmethod
    def set_value(section_name: str, key: str, value: Any) -> None:
        """Create or update a single value in a section."""
        model = ConfigManager._models.get(section_name)
        if not model:
            raise ValueError(f"Section '{section_name}' not found.")
        with Session(ConfigManager._engine) as session:
            row = session.query(model).first()
            if row is None:
                row = model(**{key: value})
                session.add(row)
            else:
                if not hasattr(row, key):
                    raise KeyError(f"Column '{key}' not found in section '{section_name}'")
                setattr(row, key, value)
            session.commit()

    @staticmethod
    def read_value(section_name: str, key: str) -> Any:
        model = ConfigManager._models.get(section_name)
        if not model:
            raise ValueError(f"Section '{section_name}' not found.")
        with Session(ConfigManager._engine) as session:
            row = session.query(model).first()
            if row is None:
                raise ValueError(f"Section '{section_name}' has no data.")
            if not hasattr(row, key):
                raise KeyError(f"Column '{key}' not found in section '{section_name}'")
            return getattr(row, key)

    @staticmethod
    def delete_value(section_name: str, key: str) -> None:
        model = ConfigManager._models.get(section_name)
        if not model:
            raise ValueError(f"Section '{section_name}' not found.")
        with Session(ConfigManager._engine) as session:
            row = session.query(model).first()
            if row is None:
                raise ValueError(f"Section '{section_name}' has no data.")
            if not hasattr(row, key):
                raise KeyError(f"Column '{key}' not found in section '{section_name}'")
            setattr(row, key, None)
            session.commit()

    @staticmethod
    def read_section(section_name: str) -> Any:
        model = ConfigManager._models.get(section_name)
        if not model:
            raise ValueError(f"Section '{section_name}' not found.")
        with Session(ConfigManager._engine) as session:
            return session.query(model).first()
