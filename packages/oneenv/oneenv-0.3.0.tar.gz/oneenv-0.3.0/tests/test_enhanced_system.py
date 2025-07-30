"""
Test cases for the enhanced OneEnv system with Pydantic models and entry-points.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock

# Import the enhanced system
from oneenv.models import EnvVarConfig, EnvTemplate, TemplateCollection
from oneenv.core import OneEnvCore, oneenv
from oneenv import template, collect_templates, generate_env_example


class TestPydanticModels:
    """Test Pydantic model validation and functionality"""
    
    def test_env_var_config_basic(self):
        """Test basic EnvVarConfig creation and validation"""
        config = EnvVarConfig(description="Test variable")
        assert config.description == "Test variable"
        assert config.default == ""
        assert config.required is False
        assert config.choices is None
    
    def test_env_var_config_with_all_fields(self):
        """Test EnvVarConfig with all fields"""
        config = EnvVarConfig(
            description="Test variable with choices",
            default="option1",
            required=True,
            choices=["option1", "option2", "option3"]
        )
        assert config.description == "Test variable with choices"
        assert config.default == "option1"
        assert config.required is True
        assert config.choices == ["option1", "option2", "option3"]
    
    def test_env_var_config_validation_empty_description(self):
        """Test that empty description raises ValueError"""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            EnvVarConfig(description="   ")
    
    def test_env_var_config_validation_empty_choices(self):
        """Test that empty choices list raises ValueError"""
        with pytest.raises(ValueError, match="Choices list cannot be empty"):
            EnvVarConfig(description="Test", choices=[])
    
    def test_env_var_config_validation_default_not_in_choices(self):
        """Test that default value must be in choices if provided"""
        with pytest.raises(ValueError, match="must be one of the choices"):
            EnvVarConfig(
                description="Test",
                default="invalid",
                choices=["valid1", "valid2"]
            )
    
    def test_env_template_creation(self):
        """Test EnvTemplate creation and validation"""
        config = EnvVarConfig(description="Test variable")
        template = EnvTemplate(
            variables={"TEST_VAR": config},
            source="test_source"
        )
        assert template.source == "test_source"
        assert "TEST_VAR" in template.variables
        assert template.variables["TEST_VAR"].description == "Test variable"
    
    def test_env_template_validation_empty_variables(self):
        """Test that empty variables dict raises ValueError"""
        with pytest.raises(ValueError, match="Template must contain at least one"):
            EnvTemplate(variables={}, source="test")
    
    def test_env_template_validation_empty_source(self):
        """Test that empty source raises ValueError"""
        config = EnvVarConfig(description="Test")
        with pytest.raises(ValueError, match="Source identifier cannot be empty"):
            EnvTemplate(variables={"TEST": config}, source="   ")


class TestTemplateCollection:
    """Test TemplateCollection functionality"""
    
    def test_template_collection_basic(self):
        """Test basic template collection operations"""
        collection = TemplateCollection()
        
        config = EnvVarConfig(description="Test variable")
        template = EnvTemplate(variables={"TEST_VAR": config}, source="test")
        
        collection.add_template(template)
        assert len(collection.templates) == 1
    
    def test_template_collection_merge(self):
        """Test merging templates from multiple sources"""
        collection = TemplateCollection()
        
        # Add first template
        config1 = EnvVarConfig(description="Variable 1")
        template1 = EnvTemplate(variables={"VAR1": config1}, source="source1")
        collection.add_template(template1)
        
        # Add second template with different variable
        config2 = EnvVarConfig(description="Variable 2")
        template2 = EnvTemplate(variables={"VAR2": config2}, source="source2")
        collection.add_template(template2)
        
        # Add third template with duplicate variable
        config3 = EnvVarConfig(description="Variable 1 duplicate")
        template3 = EnvTemplate(variables={"VAR1": config3}, source="source3")
        collection.add_template(template3)
        
        merged = collection.get_merged_variables()
        
        # Should have 2 unique variables
        assert len(merged) == 2
        assert "VAR1" in merged
        assert "VAR2" in merged
        
        # VAR1 should have 2 sources
        assert len(merged["VAR1"]["sources"]) == 2
        assert "source1" in merged["VAR1"]["sources"]
        assert "source3" in merged["VAR1"]["sources"]
        
        # VAR2 should have 1 source
        assert len(merged["VAR2"]["sources"]) == 1
        assert "source2" in merged["VAR2"]["sources"]
    
    def test_template_collection_duplicates(self):
        """Test duplicate detection"""
        collection = TemplateCollection()
        
        # Add templates with duplicate variables
        config1 = EnvVarConfig(description="Variable 1")
        template1 = EnvTemplate(variables={"DUP_VAR": config1}, source="source1")
        collection.add_template(template1)
        
        config2 = EnvVarConfig(description="Variable 1 duplicate")
        template2 = EnvTemplate(variables={"DUP_VAR": config2}, source="source2")
        collection.add_template(template2)
        
        duplicates = collection.get_duplicate_variables()
        
        assert len(duplicates) == 1
        assert "DUP_VAR" in duplicates
        assert len(duplicates["DUP_VAR"]) == 2
        assert "source1" in duplicates["DUP_VAR"]
        assert "source2" in duplicates["DUP_VAR"]
    
    def test_template_collection_description_merging(self):
        """Test description merging for duplicate variables"""
        collection = TemplateCollection()
        
        # Add first template with database variable
        config1 = EnvVarConfig(
            description="データベース接続URL",
            default="postgresql://localhost:5432/db",
            required=True,
            choices=None
        )
        template1 = EnvTemplate(variables={"DATABASE_URL": config1}, source="package-a")
        collection.add_template(template1)
        
        # Add second template with same variable but different description
        config2 = EnvVarConfig(
            description="Database connection string for the application",
            default="postgresql://...",  # Must be one of choices
            required=False,  # Different required
            choices=["postgresql://...", "mysql://..."]  # Different choices
        )
        template2 = EnvTemplate(variables={"DATABASE_URL": config2}, source="package-b")
        collection.add_template(template2)
        
        merged = collection.get_merged_variables()
        
        # Should have only one DATABASE_URL entry
        assert len(merged) == 1
        assert "DATABASE_URL" in merged
        
        # Should have both sources
        assert len(merged["DATABASE_URL"]["sources"]) == 2
        assert "package-a" in merged["DATABASE_URL"]["sources"]
        assert "package-b" in merged["DATABASE_URL"]["sources"]
        
        # Configuration should use first source's settings
        config = merged["DATABASE_URL"]["config"]
        assert config.default == "postgresql://localhost:5432/db"  # From first source
        assert config.required is True  # From first source
        assert config.choices is None  # From first source
        
        # Description should include both sources
        description = config.description
        assert "データベース接続URL" in description
        assert "Database connection string for the application" in description
        assert "From package-b:" in description


class TestOneEnvCore:
    """Test OneEnvCore functionality"""
    
    def test_oneenv_core_basic(self):
        """Test basic OneEnvCore functionality"""
        core = OneEnvCore()
        
        # Test legacy function registration
        @core.register_legacy_function
        def test_legacy():
            return {
                "LEGACY_VAR": {
                    "description": "Legacy variable",
                    "default": "legacy_value"
                }
            }
        
        legacy_templates = core.discover_legacy_templates()
        assert len(legacy_templates) == 1
        assert legacy_templates[0].source == "test_legacy"
        assert "LEGACY_VAR" in legacy_templates[0].variables
    
    def test_oneenv_core_template_generation(self):
        """Test template generation through OneEnvCore"""
        core = OneEnvCore()
        
        @core.register_legacy_function
        def test_template():
            return {
                "CORE_TEST_VAR": {
                    "description": "Core test variable",
                    "default": "core_value",
                    "required": True,
                    "choices": ["core_value", "other_value"]
                }
            }
        
        content = core.generate_env_example_content(
            discover_plugins=False,  # No plugins for this test
            discover_legacy=True,
            debug=False
        )
        
        assert "# Auto-generated by OneEnv" in content
        assert "CORE_TEST_VAR=core_value" in content
        assert "# Core test variable" in content
        assert "# Required" in content
        assert "# Choices: core_value, other_value" in content
    
    @patch('oneenv.core.entry_points')
    def test_oneenv_core_entry_points(self, mock_entry_points):
        """Test entry-points discovery"""
        # Mock entry-point
        mock_ep = MagicMock()
        mock_ep.name = "test_plugin"
        mock_ep.load.return_value = lambda: {
            "PLUGIN_VAR": {
                "description": "Plugin variable",
                "default": "plugin_value"
            }
        }
        
        mock_entry_points.return_value = [mock_ep]
        
        core = OneEnvCore()
        plugin_templates = core.discover_entry_point_templates()
        
        assert len(plugin_templates) == 1
        assert plugin_templates[0].source == "plugin:test_plugin"
        assert "PLUGIN_VAR" in plugin_templates[0].variables


class TestEnhancedIntegration:
    """Test integration with the enhanced system through main interface"""
    
    def setUp(self):
        """Set up each test by clearing the registry"""
        # Clear the registry before each test
        from oneenv.core import _oneenv_core
        _oneenv_core._legacy_registry.clear()
    
    def test_enhanced_decorator_integration(self):
        """Test that the enhanced decorator works with the main interface"""
        self.setUp()
        
        @oneenv
        def integration_test():
            return {
                "INTEGRATION_VAR": {
                    "description": "Integration test variable",
                    "default": "integration_value",
                    "required": False
                }
            }
        
        # Test template generation
        content = template(debug=False)
        assert "INTEGRATION_VAR=integration_value" in content
        assert "# Integration test variable" in content
        
        # Test collection
        templates = collect_templates()
        assert "INTEGRATION_VAR" in templates
        assert templates["INTEGRATION_VAR"]["config"]["description"] == "Integration test variable"
    
    def test_enhanced_file_generation(self):
        """Test file generation with enhanced system"""
        self.setUp()
        
        @oneenv
        def file_test():
            return {
                "FILE_TEST_VAR": {
                    "description": "File test variable",
                    "default": "file_value"
                }
            }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env.example', delete=False) as f:
            output_path = f.name
        
        try:
            generate_env_example(output_path, debug=False)
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert "FILE_TEST_VAR=file_value" in content
            assert "# File test variable" in content
            
        finally:
            os.unlink(output_path)
    
    def test_duplicate_variable_merging_integration(self):
        """Test that duplicate variables are properly merged in final output"""
        self.setUp()
        
        # Define two templates with the same variable
        @oneenv
        def web_template():
            return {
                "DATABASE_URL": {
                    "description": "Web application database URL",
                    "default": "sqlite:///web.db",
                    "required": True
                },
                "PORT": {
                    "description": "Web server port",
                    "default": "8000",
                    "required": False
                }
            }
        
        @oneenv
        def api_template():
            return {
                "DATABASE_URL": {
                    "description": "API database connection string",
                    "default": "postgresql://localhost:5432/api",
                    "required": False
                },
                "API_KEY": {
                    "description": "API authentication key",
                    "default": "",
                    "required": True
                }
            }
        
        # Generate template content
        content = template(debug=False)
        
        # DATABASE_URL should appear only once
        database_url_count = content.count("DATABASE_URL=")
        assert database_url_count == 1, f"DATABASE_URL should appear once, but found {database_url_count} times"
        
        # Should contain descriptions from both sources
        assert "Web application database URL" in content
        assert "API database connection string" in content
        assert "From api_template:" in content
        
        # Should use first template's configuration (web_template was defined first)
        assert "DATABASE_URL=sqlite:///web.db" in content
        
        # Should also contain unique variables from both templates
        assert "PORT=8000" in content
        assert "API_KEY=" in content
        
        # Should show both sources for DATABASE_URL
        assert "(Defined in: api_template, web_template)" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])