"""
OneEnv Core Module with Pydantic Models and Entry-points Support

Enhanced version of OneEnv that supports both legacy decorator-based templates
and new entry-points based plugins with Pydantic model validation.
"""

import sys
from typing import Dict, List, Any, Optional, Callable

# Handle different Python versions for importlib.metadata
if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

try:
    from .models import (
        EnvVarConfig, 
        EnvTemplate, 
        TemplateCollection,
        dict_to_env_var_config,
        env_var_config_to_dict,
        template_function_to_env_template
    )
except ImportError:
    # Fallback for development/testing
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from models import (
        EnvVarConfig, 
        EnvTemplate, 
        TemplateCollection,
        dict_to_env_var_config,
        env_var_config_to_dict,
        template_function_to_env_template
    )


class OneEnvCore:
    """
    Core OneEnv functionality with support for both legacy and new systems
    レガシーシステムと新システムの両方をサポートするOneEnvコア機能
    """
    
    def __init__(self, entry_point_group: str = "oneenv.templates"):
        self.entry_point_group = entry_point_group
        self.template_collection = TemplateCollection()
        self._legacy_registry: List[Callable] = []
    
    def register_legacy_function(self, func: Callable) -> Callable:
        """
        Register a legacy decorator-based template function
        レガシーデコレータベースのテンプレート関数を登録
        """
        self._legacy_registry.append(func)
        return func
    
    def discover_entry_point_templates(self, debug: bool = False) -> List[EnvTemplate]:
        """
        Discover and load templates from entry-points
        Entry-pointsからテンプレートを発見・読み込み
        """
        discovered_templates = []
        
        try:
            template_eps = entry_points(group=self.entry_point_group)
            
            for ep in template_eps:
                try:
                    # Load the entry-point function
                    template_func = ep.load()
                    
                    # Call the function to get template data
                    template_result = template_func()
                    
                    # Convert to EnvTemplate with validation
                    env_template = self._convert_template_result_to_model(
                        template_result, f"plugin:{ep.name}"
                    )
                    
                    discovered_templates.append(env_template)
                    
                    if debug:
                        print(f"Loaded template plugin: {ep.name}")
                        
                except Exception as e:
                    if debug:
                        print(f"Failed to load template plugin {ep.name}: {e}")
                        
        except Exception as e:
            if debug:
                print(f"Error discovering template plugins: {e}")
        
        return discovered_templates
    
    def discover_legacy_templates(self, debug: bool = False) -> List[EnvTemplate]:
        """
        Convert legacy decorator-based templates to EnvTemplate models
        レガシーデコレータベースのテンプレートをEnvTemplateモデルに変換
        """
        legacy_templates = []
        
        for func in self._legacy_registry:
            try:
                # Call the legacy function
                template_dict = func()
                
                # Convert to EnvTemplate with validation
                env_template = template_function_to_env_template(func.__name__, template_dict)
                legacy_templates.append(env_template)
                
                if debug:
                    print(f"Loaded legacy template: {func.__name__}")
                    
            except Exception as e:
                if debug:
                    print(f"Failed to load legacy template {func.__name__}: {e}")
        
        return legacy_templates
    
    def _convert_template_result_to_model(self, template_result: Any, source: str) -> EnvTemplate:
        """
        Convert template function result to EnvTemplate model with validation
        テンプレート関数の結果をEnvTemplateモデルに変換（検証付き）
        """
        if isinstance(template_result, dict):
            # Legacy dictionary format
            variables = {}
            for var_name, var_config in template_result.items():
                if isinstance(var_config, dict):
                    # Convert dict to EnvVarConfig with validation
                    variables[var_name] = dict_to_env_var_config(var_config)
                elif isinstance(var_config, EnvVarConfig):
                    # Already a model
                    variables[var_name] = var_config
                else:
                    raise ValueError(f"Invalid config type for {var_name}: {type(var_config)}")
            
            return EnvTemplate(variables=variables, source=source)
        
        elif isinstance(template_result, EnvTemplate):
            # Already an EnvTemplate
            template_result.source = source  # Override source
            return template_result
        
        else:
            raise ValueError(f"Invalid template result type: {type(template_result)}")
    
    def collect_all_templates(self, 
                            discover_plugins: bool = True, 
                            discover_legacy: bool = True,
                            debug: bool = False) -> TemplateCollection:
        """
        Collect templates from all sources (legacy and plugins)
        すべてのソース（レガシーとプラグイン）からテンプレートを収集
        """
        collection = TemplateCollection()
        
        # Collect legacy templates
        if discover_legacy:
            legacy_templates = self.discover_legacy_templates(debug)
            for template in legacy_templates:
                collection.add_template(template)
        
        # Collect plugin templates
        if discover_plugins:
            plugin_templates = self.discover_entry_point_templates(debug)
            for template in plugin_templates:
                collection.add_template(template)
        
        # Validate all templates
        validation_errors = collection.validate_all_templates()
        if validation_errors and debug:
            print("Template validation errors:")
            for error in validation_errors:
                print(f"  - {error}")
        
        return collection
    
    def generate_env_example_content(self, 
                                   discover_plugins: bool = True,
                                   discover_legacy: bool = True,
                                   debug: bool = False) -> str:
        """
        Generate .env.example content with enhanced template processing
        拡張されたテンプレート処理で.env.exampleコンテンツを生成
        """
        if debug:
            print("\nDiscovering templates from all sources...")
        
        # Collect all templates
        collection = self.collect_all_templates(discover_plugins, discover_legacy, debug)
        
        if debug:
            legacy_count = len(self._legacy_registry) if discover_legacy else 0
            plugin_count = len(collection.templates) - legacy_count if discover_plugins else 0
            
            print(f"\nTemplate sources:")
            print(f"  - Legacy decorator functions: {legacy_count}")
            print(f"  - Plugin entry-point functions: {plugin_count}")
            
            # Report duplicates
            duplicates = collection.get_duplicate_variables()
            if duplicates:
                print(f"\nDuplicate variables found:")
                for var_name, sources in duplicates.items():
                    print(f"  - {var_name}: {', '.join(sources)}")
            print("")
        
        # Get merged variables
        merged_variables = collection.get_merged_variables()
        
        # Group variables by their sources, but ensure duplicates appear only once
        # Sort variables by name for consistent output
        sorted_variables = sorted(merged_variables.items())
        
        # Generate content
        lines = []
        lines.append("# Auto-generated by OneEnv")
        lines.append("")
        
        # Process each variable once, with aggregated information
        for var_name, info in sorted_variables:
            config = info["config"]
            sources = info["sources"]
            
            # Add source information
            sources_str = ", ".join(sorted(sources))
            lines.append(f"# (Defined in: {sources_str})")
            
            # Use Pydantic model attributes
            description = config.description
            default_value = config.default
            required_value = config.required
            choices_value = config.choices
            
            # Add description lines (now includes merged descriptions from all sources)
            for line in description.splitlines():
                stripped_line = line.strip()
                if stripped_line:
                    # Skip source attribution lines that start with "# From"
                    if not stripped_line.startswith("# From "):
                        lines.append(f"# {stripped_line}")
                    else:
                        # Add source attribution as-is
                        lines.append(f"{stripped_line}")
            
            # Add required marker
            if required_value:
                lines.append("# Required")
            
            # Add choices
            if choices_value:
                lines.append(f"# Choices: {', '.join(choices_value)}")
            
            # Add variable assignment
            lines.append(f"{var_name}={default_value}")
            lines.append("")
        
        return "\n".join(lines)
    
    def get_legacy_compatible_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Return templates in legacy dictionary format for backward compatibility
        後方互換性のためにレガシー辞書形式でテンプレートを返す
        """
        collection = self.collect_all_templates()
        merged_variables = collection.get_merged_variables()
        
        legacy_format = {}
        for var_name, info in merged_variables.items():
            legacy_format[var_name] = {
                "config": env_var_config_to_dict(info["config"]),
                "sources": info["sources"]
            }
        
        return legacy_format


# Global instance for compatibility with existing API
_oneenv_core = OneEnvCore()

# Decorator for legacy compatibility
def oneenv(func: Callable) -> Callable:
    """
    Legacy decorator for registering template functions
    テンプレート関数を登録するレガシーデコレータ
    """
    return _oneenv_core.register_legacy_function(func)

# Enhanced functions that use the new core
def collect_templates_enhanced(debug: bool = False) -> Dict[str, Dict[str, Any]]:
    """Enhanced version of collect_templates using Pydantic models"""
    return _oneenv_core.get_legacy_compatible_templates()

def template_enhanced(debug: bool = False) -> str:
    """Enhanced version of template generation using Pydantic models"""
    return _oneenv_core.generate_env_example_content(debug=debug)

def report_duplicates_enhanced(debug: bool = False) -> None:
    """Enhanced version of duplicate reporting"""
    collection = _oneenv_core.collect_all_templates(debug=debug)
    duplicates = collection.get_duplicate_variables()
    
    for var_name, sources in duplicates.items():
        print(f"Warning: Duplicate key '{var_name}' defined in {', '.join(sources)}")

# Export the global registry for backward compatibility
def get_template_registry() -> List[Callable]:
    """Get the legacy template function registry"""
    return _oneenv_core._legacy_registry

def clear_template_registry() -> None:
    """Clear the legacy template function registry (useful for testing)"""
    _oneenv_core._legacy_registry.clear()