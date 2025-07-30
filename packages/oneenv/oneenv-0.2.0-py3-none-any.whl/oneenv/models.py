"""
OneEnv Pydantic Models for Environment Variable Templates

This module defines Pydantic models for type-safe environment variable templates.
環境変数テンプレート用のPydanticモデルを定義するモジュールです。
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator
import sys

if sys.version_info < (3, 10):
    from typing_extensions import Literal
else:
    from typing import Literal


class EnvVarConfig(BaseModel):
    """
    Configuration for a single environment variable
    単一の環境変数の設定
    """
    description: str = Field(
        ..., 
        min_length=1,
        description="Description of the environment variable (required)"
    )
    default: str = Field(
        default="",
        description="Default value for the environment variable"
    )
    required: bool = Field(
        default=False,
        description="Whether this environment variable is required"
    )
    choices: Optional[List[str]] = Field(
        default=None,
        description="List of valid choices for this environment variable"
    )
    
    @field_validator('description')
    @classmethod
    def description_must_not_be_empty(cls, v):
        """Ensure description is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()
    
    @field_validator('choices')
    @classmethod
    def choices_must_not_be_empty(cls, v):
        """If choices are provided, they must not be an empty list"""
        if v is not None and len(v) == 0:
            raise ValueError('Choices list cannot be empty if provided')
        return v
    
    @model_validator(mode='after')
    def validate_default_in_choices(self):
        """If choices are provided and default is not empty, it must be in choices"""
        if self.choices and self.default and self.default not in self.choices:
            raise ValueError(f'Default value "{self.default}" must be one of the choices: {self.choices}')
        return self


class EnvTemplate(BaseModel):
    """
    Template containing multiple environment variables
    複数の環境変数を含むテンプレート
    """
    variables: Dict[str, EnvVarConfig] = Field(
        ...,
        description="Dictionary of environment variable names to their configurations"
    )
    source: str = Field(
        ...,
        description="Source identifier for this template (function name, plugin name, etc.)"
    )
    
    @field_validator('variables')
    @classmethod
    def variables_must_not_be_empty(cls, v):
        """Template must contain at least one environment variable"""
        if not v:
            raise ValueError('Template must contain at least one environment variable')
        return v
    
    @field_validator('source')
    @classmethod
    def source_must_not_be_empty(cls, v):
        """Source identifier must not be empty"""
        if not v.strip():
            raise ValueError('Source identifier cannot be empty')
        return v.strip()


class TemplateCollection(BaseModel):
    """
    Collection of templates from various sources with conflict resolution
    複数のソースからのテンプレートコレクション（競合解決機能付き）
    """
    templates: List[EnvTemplate] = Field(
        default_factory=list,
        description="List of environment variable templates"
    )
    
    def add_template(self, template: EnvTemplate) -> None:
        """Add a template to the collection"""
        self.templates.append(template)
    
    def get_merged_variables(self) -> Dict[str, Dict[str, Any]]:
        """
        Merge all templates and return variables with their sources
        重複した変数は説明を集約し、他の設定は最初のパッケージの情報を使用
        
        Returns:
            Dict[var_name, {"config": EnvVarConfig, "sources": List[str]}]
        """
        merged = {}
        
        for template in self.templates:
            for var_name, var_config in template.variables.items():
                if var_name in merged:
                    # Variable already exists - merge descriptions and track sources
                    existing_config = merged[var_name]["config"]
                    
                    # Collect descriptions from all sources
                    existing_desc = existing_config.description.strip()
                    new_desc = var_config.description.strip()
                    
                    # Merge descriptions if they're different
                    if new_desc and new_desc not in existing_desc:
                        merged_description = f"{existing_desc}\n\n# From {template.source}:\n{new_desc}"
                    else:
                        merged_description = existing_desc
                    
                    # Create new config with merged description but keep other settings from first source
                    merged_config = EnvVarConfig(
                        description=merged_description,
                        default=existing_config.default,  # Keep first source's default
                        required=existing_config.required,  # Keep first source's required
                        choices=existing_config.choices    # Keep first source's choices
                    )
                    
                    merged[var_name]["config"] = merged_config
                    
                    # Add source if not already present
                    if template.source not in merged[var_name]["sources"]:
                        merged[var_name]["sources"].append(template.source)
                else:
                    # New variable
                    merged[var_name] = {
                        "config": var_config,
                        "sources": [template.source]
                    }
        
        return merged
    
    def get_duplicate_variables(self) -> Dict[str, List[str]]:
        """
        Get variables that are defined in multiple sources
        複数のソースで定義されている変数を取得
        
        Returns:
            Dict[var_name, List[source_names]]
        """
        merged = self.get_merged_variables()
        return {
            var_name: info["sources"]
            for var_name, info in merged.items()
            if len(info["sources"]) > 1
        }
    
    def validate_all_templates(self) -> List[str]:
        """
        Validate all templates and return list of validation errors
        すべてのテンプレートを検証し、検証エラーのリストを返す
        
        Returns:
            List of error messages
        """
        errors = []
        
        for i, template in enumerate(self.templates):
            try:
                # Pydantic validation is automatic, but we can add custom checks
                if not template.variables:
                    errors.append(f"Template {i} from source '{template.source}' has no variables")
            except Exception as e:
                errors.append(f"Template {i} from source '{template.source}' validation error: {str(e)}")
        
        return errors


# Legacy compatibility functions for existing dictionary-based system
def dict_to_env_var_config(config_dict: Dict[str, Any]) -> EnvVarConfig:
    """
    Convert legacy dictionary configuration to EnvVarConfig model
    レガシーの辞書設定をEnvVarConfigモデルに変換
    """
    return EnvVarConfig(**config_dict)


def env_var_config_to_dict(config: EnvVarConfig) -> Dict[str, Any]:
    """
    Convert EnvVarConfig model to dictionary (for backward compatibility)
    EnvVarConfigモデルを辞書に変換（後方互換性のため）
    """
    result = {
        "description": config.description,
        "default": config.default,
        "required": config.required,
    }
    
    if config.choices is not None:
        result["choices"] = config.choices
    
    return result


def template_function_to_env_template(func_name: str, template_dict: Dict[str, Dict[str, Any]]) -> EnvTemplate:
    """
    Convert legacy template function result to EnvTemplate model
    レガシーのテンプレート関数結果をEnvTemplateモデルに変換
    """
    variables = {
        var_name: dict_to_env_var_config(var_config)
        for var_name, var_config in template_dict.items()
    }
    
    return EnvTemplate(
        variables=variables,
        source=func_name
    )


# Example usage and validation
if __name__ == "__main__":
    # Example environment variable configuration
    example_config = EnvVarConfig(
        description="Database connection URL",
        default="postgresql://localhost:5432/mydb",
        required=True,
        choices=None
    )
    
    print("Example EnvVarConfig:")
    print(example_config.json(indent=2))
    
    # Example template
    example_template = EnvTemplate(
        variables={
            "DATABASE_URL": example_config,
            "DEBUG_MODE": EnvVarConfig(
                description="Enable debug mode",
                default="false",
                required=False,
                choices=["true", "false"]
            )
        },
        source="example_template"
    )
    
    print("\nExample EnvTemplate:")
    print(example_template.json(indent=2))
    
    # Example collection
    collection = TemplateCollection()
    collection.add_template(example_template)
    
    merged = collection.get_merged_variables()
    print("\nMerged variables:")
    for var_name, info in merged.items():
        print(f"  {var_name}: {info['config'].description} (from: {', '.join(info['sources'])})")