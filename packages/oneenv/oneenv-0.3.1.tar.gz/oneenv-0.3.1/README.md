# OneEnv 🌟　[![PyPI Downloads](https://static.pepy.tech/badge/oneenv)](https://pepy.tech/projects/oneenv)

OneEnv is a **revolutionary environment variable management tool** for Python applications that makes configuration management **incredibly simple**. It automatically discovers and consolidates environment variable templates from all your installed packages into a single `.env.example` file - **no manual configuration required**!

## Why OneEnv Makes Your Life Easier 🚀

**Before OneEnv:**
- 😓 Manual creation of `.env.example` files for each project
- 😤 Hunting through documentation to find required environment variables
- 😱 Missing critical configuration when integrating new packages
- 🤯 Inconsistent environment variable formats across projects

**After OneEnv:**
- ✨ **Automatic discovery** of environment variables from all packages
- 🎯 **One command** generates complete `.env.example` files
- 🔄 **Smart merging** of duplicate variables with detailed descriptions
- 📦 **Plugin ecosystem** where packages provide their own templates
- 🛡️ **Type safety** with Pydantic validation

## Revolutionary Features 🌟

### 🔌 **Plugin System with Entry-points**
Packages can automatically provide their environment variable templates - just install and use!

### 🎨 **Smart Duplicate Handling**
When multiple packages define the same variable, OneEnv intelligently merges descriptions while keeping configuration consistent.

### ⚡ **Zero Configuration Setup**
Install a package with OneEnv templates? They're automatically discovered. No imports, no manual registration needed.

### 🔒 **Type-Safe Templates**
Built with Pydantic models for runtime validation and better error messages.

### 📋 **Legacy Decorator Support**
Existing `@oneenv` decorators continue to work seamlessly alongside the new plugin system.

## Supported Environments 🖥️

- **Python**: ≥ 3.10
- **Operating Systems**: Windows, macOS, Linux

## Installation 📦

You can install OneEnv easily via pip:

```bash
pip install oneenv
```

For development mode, install from the source using:

```bash
pip install -e .
```

## Super Simple Usage 🎯

### Step 1: Install Packages with OneEnv Support
```bash
pip install oneenv
pip install django-oneenv-plugin  # Example: Django templates
pip install fastapi-oneenv-plugin # Example: FastAPI templates
```

### Step 2: Generate Your Environment Template
```bash
oneenv template
```

**That's it!** 🎉 OneEnv automatically discovers all environment variables from your installed packages and creates a complete `.env.example` file.

## Advanced Usage 🚀

### 🔍 See What's Discovered
```bash
oneenv template -d
```
This shows you:
- 📦 Which plugins were discovered
- 🔄 Which variables are duplicated across packages
- ⚡ Template generation process

### 📝 Custom Output File
```bash
oneenv template -o my-custom.env
```

### 🔄 Compare Environment Files
```bash
oneenv diff old.env new.env
```

## For Package Developers: Creating OneEnv Plugins 📦

### Method 1: Modern Plugin System (Recommended) ⭐

Create environment templates that are automatically discovered:

**1. Create your template function:**
```python
# mypackage/templates.py

# Option A: New Groups Format (Recommended) ⭐
def database_template():
    """Database configuration template"""
    return {
        "groups": {
            "Database": {
                "DATABASE_URL": {
                    "description": "Database connection URL\nExample: postgresql://user:pass@localhost:5432/db",
                    "default": "sqlite:///app.db",
                    "required": True,
                    "importance": "critical"
                },
                "DB_POOL_SIZE": {
                    "description": "Database connection pool size",
                    "default": "10",
                    "required": False,
                    "choices": ["5", "10", "20", "50"],
                    "importance": "important"
                }
            },
            "Cache": {
                "REDIS_URL": {
                    "description": "Redis connection URL",
                    "default": "redis://localhost:6379/0",
                    "importance": "important"
                }
            }
        }
    }

# Option B: Traditional Format (Still Supported)
def legacy_template():
    """Legacy format template"""
    return {
        "DATABASE_URL": {
            "description": "Database connection URL",
            "default": "sqlite:///app.db",
            "required": True,
            "group": "Database",
            "importance": "critical"
        }
    }
```

**2. Register in pyproject.toml:**
```toml
[project.entry-points."oneenv.templates"]
database = "mypackage.templates:database_template"
redis = "mypackage.templates:redis_template"
```

**3. That's it!** 🎉 When users install your package, OneEnv automatically discovers your templates.

### Method 2: Legacy Decorator System 📋

Still supported for backward compatibility:

```python
from oneenv import oneenv

@oneenv
def my_env_template():
    return {
        "MY_API_KEY": {
            "description": "API key for accessing the service",
            "default": "",
            "required": True
        },
        "MODE": {
            "description": "Application mode setting",
            "default": "development",
            "required": False,
            "choices": ["development", "production"]
        }
    }
```

## Smart Duplicate Variable Handling 🎨

When multiple packages define the same environment variable, OneEnv intelligently merges them:

**Example Output:**
```bash
# Auto-generated by OneEnv

# (Defined in: django-plugin, fastapi-plugin)
# Django database connection URL
# Example: postgresql://user:pass@localhost:5432/django_db
# From fastapi-plugin:
# FastAPI application database connection
# Supports: PostgreSQL, MySQL, SQLite
# Required
DATABASE_URL=sqlite:///django.db

# (Defined in: redis-plugin)
# Redis connection URL
# Example: redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/0
```

**How it works:**
- ✅ **Single entry**: Each variable appears only once
- 📝 **Merged descriptions**: All package descriptions are combined
- ⚙️ **First wins**: Configuration (default, required, choices) uses the first package's settings
- 📋 **Source tracking**: Shows which packages define each variable

## Template Field Reference 📚

### Basic Template (v0.1.x - v0.2.x)
```python
{
    "VARIABLE_NAME": {
        "description": "Clear description of what this variable does",  # Required
        "default": "default_value",      # Optional: Default value
        "required": True,                # Optional: Whether required (default: False)
        "choices": ["option1", "option2"] # Optional: Valid choices
    }
}
```

### Enhanced Template (v0.3.0+)

#### Traditional Enhanced Format
```python
{
    "VARIABLE_NAME": {
        "description": "Clear description of what this variable does",  # Required
        "default": "default_value",      # Optional: Default value
        "required": True,                # Optional: Whether required (default: False)
        "choices": ["option1", "option2"], # Optional: Valid choices
        "group": "Category Name",        # NEW: Group for organization
        "importance": "critical"         # NEW: critical/important/optional
    }
}
```

#### New Groups Format (v0.3.1+) ⭐
```python
{
    "groups": {
        "Database": {
            "DATABASE_URL": {
                "description": "Database connection URL",
                "default": "postgresql://localhost:5432/mydb",
                "required": True,
                "importance": "critical"
            },
            "DB_POOL_SIZE": {
                "description": "Maximum database connections",
                "default": "10",
                "importance": "important"
            }
        },
        "Security": {
            "SECRET_KEY": {
                "description": "Application secret key",
                "required": True,
                "importance": "critical"
            }
        }
    }
}
```

#### Mixed Format (Both Supported)
```python
{
    # Direct variables (assigned to default group)
    "GLOBAL_VAR": {
        "description": "Global setting",
        "group": "Application",  # Explicit group assignment
        "importance": "critical"
    },
    
    # Grouped variables
    "groups": {
        "Database": {
            "DATABASE_URL": {...}
        }
    }
}
```

### Importance Levels
- **`critical`**: Essential settings for application operation (必須設定項目)
- **`important`**: Settings to configure for production use (重要設定項目)  
- **`optional`**: Fine-tuning settings where defaults are sufficient (デフォルトで十分)

## Real-World Examples 🌍

### Django + FastAPI + Redis Project
```bash
pip install oneenv django-oneenv fastapi-oneenv redis-oneenv
oneenv template
```

**Generated .env.example (v0.3.0 with grouping):**
```bash
# Auto-generated by OneEnv

# ========== CRITICAL: Essential Settings for Application Operation ==========

# ----- Database -----

# (Defined in: django-oneenv, fastapi-oneenv)
# Django database connection URL
# From fastapi-oneenv: FastAPI database connection
# Required
DATABASE_URL=sqlite:///django.db

# ----- Security -----

# (Defined in: django-oneenv)
# Django secret key for security
# Required
SECRET_KEY=your-secret-key-here

# ========== IMPORTANT: Settings to Configure for Production Use ==========

# ----- Cache -----

# (Defined in: redis-oneenv)
# Redis connection for caching and sessions
REDIS_URL=redis://localhost:6379/0
```

### Custom Project Templates (v0.3.1 Enhanced)
```python
# myproject/env_templates.py
from oneenv import oneenv

# New Groups Format (Recommended)
@oneenv
def custom_project_config():
    return {
        "groups": {
            "Application": {
                "PROJECT_NAME": {
                    "description": "Name of your awesome project",
                    "default": "My Awesome App",
                    "required": True,
                    "importance": "critical"
                },
                "ENVIRONMENT": {
                    "description": "Deployment environment",
                    "default": "development",
                    "choices": ["development", "staging", "production"],
                    "importance": "important"
                }
            },
            "Logging": {
                "LOG_ROTATION_DAYS": {
                    "description": "Number of days to keep log files",
                    "default": "30",
                    "required": False,
                    "importance": "optional"
                },
                "LOG_LEVEL": {
                    "description": "Application logging level",
                    "default": "INFO",
                    "choices": ["DEBUG", "INFO", "WARNING", "ERROR"],
                    "importance": "optional"
                }
            }
        }
    }

# Traditional Format (Still Supported)
@oneenv
def legacy_project_config():
    return {
        "PROJECT_NAME": {
            "description": "Name of your awesome project",
            "default": "My Awesome App",
            "required": True,
            "group": "Application",
            "importance": "critical"
        }
    }
```

## Integration with dotenv 🔄

OneEnv wraps [python-dotenv](https://github.com/theskumar/python-dotenv), so you can use all dotenv features directly:

```python
from oneenv import load_dotenv, dotenv_values

# Load environment variables
load_dotenv()

# Get variables as dictionary
config = dotenv_values(".env")
```

## What's New in v0.3.1 🆕

### 🏗️ **Revolutionary Groups Format**
One function can now define multiple groups, making template organization incredibly flexible:

```python
@oneenv
def complete_webapp_config():
    return {
        "groups": {
            "Database": {
                "DATABASE_URL": {...},
                "DB_POOL_SIZE": {...}
            },
            "Security": {
                "SECRET_KEY": {...},
                "JWT_EXPIRY": {...}
            },
            "Cache": {
                "REDIS_URL": {...}
            }
        }
    }
```

**Benefits:**
- **📦 Single Source**: One function defines all related variables
- **🎯 Logical Grouping**: Variables are automatically organized by purpose
- **🔄 Backward Compatible**: Traditional format still works perfectly
- **🚀 Entry-Point Friendly**: Fewer entry-point registrations needed

### 🎯 **Smart Organization & Prioritization (v0.3.0)**
Environment variables are intelligently organized by importance and grouped by category:

- **📊 Enhanced Grouping**: Both traditional and new groups format supported
- **⚡ Importance Levels**: 
  - `critical`: Essential for application operation
  - `important`: Should be configured for production
  - `optional`: Fine-tuning settings (defaults are sufficient)
- **🌐 Multilingual Headers**: Automatic locale detection with Japanese/English support

### 📋 **Enhanced Template Format**
```python
@oneenv
def advanced_template():
    return {
        "DATABASE_URL": {
            "description": "Primary database connection",
            "default": "postgresql://localhost:5432/mydb",
            "required": True,
            "group": "Database",        # NEW: Group organization
            "importance": "critical"    # NEW: Priority level
        },
        "LOG_LEVEL": {
            "description": "Application logging level",
            "default": "INFO",
            "required": False,
            "group": "Logging",
            "importance": "important"
        }
    }
```

### 🌍 **Multilingual Support**
**Japanese Environment:**
```
# ========== CRITICAL: 必須設定項目 ==========
# ========== IMPORTANT: 重要設定項目 ==========
# ========== OPTIONAL: デフォルトで十分 ==========
```

**English Environment:**
```
# ========== CRITICAL: Essential Settings for Application Operation ==========
# ========== IMPORTANT: Settings to Configure for Production Use ==========
# ========== OPTIONAL: Fine-tuning Settings (Defaults are Sufficient) ==========
```

### 🔄 **Perfect Backward Compatibility**
All existing templates work unchanged! New features use sensible defaults:
- `group`: "General" (if not specified)
- `importance`: "important" (if not specified)

## Previous Updates

### v0.2.0: Revolutionary Plugin System
- **Entry-points Integration**: Packages automatically provide environment variable templates
- **Smart Duplicate Handling**: Intelligent merging of variables from multiple packages
- **Pydantic Type Safety**: Runtime validation with clear error messages
- **Zero Configuration**: Automatic discovery - no imports or manual registration needed

## Why OneEnv is Game-Changing 🎯

- **🚫 No more hunting**: Environment variables are automatically documented
- **⚡ Zero setup time**: Install packages, run one command, done
- **🔄 Stay synchronized**: Environment configs update automatically with package updates
- **👥 Team harmony**: Everyone gets the same environment setup
- **📦 Ecosystem growth**: Package authors can provide better configuration experiences

## Running Tests 🧪

```bash
pytest tests
```

## Contributing 🤝

We welcome contributions! Please feel free to submit a Pull Request or open an issue on GitHub.

## License ⚖️

This project is released under the MIT License.