from pathlib import Path
import os
from typing import Type
from pydantic import BaseModel
from .loaders import load_yaml

class Octus:
    @classmethod
    def load(cls, base_path: str = ".", env_var: str = "ENV_TYPE", config_model: Type[BaseModel] = BaseModel) -> BaseModel:
        base_path_obj = Path(base_path)
        
        config_file = base_path_obj / "config.yaml"
        
        if env_value := os.getenv(env_var):
            env_config = base_path_obj / f"config.{env_value}.yaml"
            if env_config.exists():
                config_file = env_config
        
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_file}")
        
        config_data = load_yaml(config_file)
        
        return config_model(**config_data)