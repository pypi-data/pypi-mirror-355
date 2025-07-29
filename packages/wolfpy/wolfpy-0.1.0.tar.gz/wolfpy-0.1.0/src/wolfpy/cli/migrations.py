"""
WolfPy Migration CLI Commands.

Command-line interface for database migrations.
"""

import os
import sys
import importlib.util
from typing import List, Type
from ..core.database import Database, Model
from ..core.migrations import MigrationManager, CreateTableMigration


def load_models_from_file(file_path: str) -> List[Type[Model]]:
    """
    Load model classes from a Python file.
    
    Args:
        file_path: Path to Python file containing models
        
    Returns:
        List of model classes
    """
    models = []
    
    if not os.path.exists(file_path):
        return models
    
    # Load the module
    spec = importlib.util.spec_from_file_location("models", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find model classes
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (isinstance(attr, type) and 
            issubclass(attr, Model) and 
            attr != Model):
            models.append(attr)
    
    return models


def load_app_models(app_file: str = 'app.py') -> List[Type[Model]]:
    """
    Load models from application file.
    
    Args:
        app_file: Path to application file
        
    Returns:
        List of model classes
    """
    models = []
    
    if not os.path.exists(app_file):
        print(f"Warning: Application file '{app_file}' not found")
        return models
    
    # Add current directory to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(app_file)))
    
    try:
        # Load the module
        spec = importlib.util.spec_from_file_location("app", app_file)
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        # Find model classes
        for attr_name in dir(app_module):
            attr = getattr(app_module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Model) and 
                attr != Model):
                models.append(attr)
    
    except Exception as e:
        print(f"Error loading models from {app_file}: {e}")
    
    return models


def makemigrations(name: str, app_file: str = 'app.py', models_file: str = None):
    """
    Generate new migration files.
    
    Args:
        name: Migration name
        app_file: Application file to scan for models
        models_file: Specific models file to scan
    """
    print(f"Generating migration: {name}")
    
    # Load models
    models = []
    if models_file:
        models.extend(load_models_from_file(models_file))
    else:
        models.extend(load_app_models(app_file))
    
    if not models:
        print("No models found. Creating empty migration.")
    else:
        print(f"Found {len(models)} models: {', '.join(m.__name__ for m in models)}")
    
    # Initialize database and migration manager
    db = Database()
    manager = MigrationManager(db)
    
    # Generate migration file
    migration_file = manager.generate_migration(name, models)
    print(f"Migration created: {migration_file}")


def migrate(app_file: str = 'app.py'):
    """
    Apply pending migrations.
    
    Args:
        app_file: Application file
    """
    print("Applying migrations...")
    
    # Initialize database
    db = Database()
    manager = MigrationManager(db)
    
    # Load migration files
    load_migration_files(manager)
    
    # Apply migrations
    manager.migrate()


def rollback(steps: int = 1, app_file: str = 'app.py'):
    """
    Rollback migrations.
    
    Args:
        steps: Number of migrations to rollback
        app_file: Application file
    """
    print(f"Rolling back {steps} migration(s)...")
    
    # Initialize database
    db = Database()
    manager = MigrationManager(db)
    
    # Load migration files
    load_migration_files(manager)
    
    # Rollback migrations
    manager.rollback(steps)


def showmigrations(app_file: str = 'app.py'):
    """
    Show migration status.
    
    Args:
        app_file: Application file
    """
    print("Migration status:")
    
    # Initialize database
    db = Database()
    manager = MigrationManager(db)
    
    # Load migration files
    load_migration_files(manager)
    
    # Show status
    manager.status()


def load_migration_files(manager: MigrationManager):
    """
    Load migration files from migrations directory.
    
    Args:
        manager: Migration manager instance
    """
    migrations_dir = manager.migrations_dir
    
    if not os.path.exists(migrations_dir):
        print(f"Migrations directory '{migrations_dir}' not found.")
        return
    
    # Load migration files
    migration_files = [f for f in os.listdir(migrations_dir) if f.endswith('.py') and not f.startswith('__')]
    migration_files.sort()
    
    for filename in migration_files:
        filepath = os.path.join(migrations_dir, filename)
        
        try:
            # Load migration module
            spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
            migration_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(migration_module)
            
            # Get migration instance
            if hasattr(migration_module, 'migration'):
                manager.add_migration(migration_module.migration)
            else:
                print(f"Warning: No migration instance found in {filename}")
        
        except Exception as e:
            print(f"Error loading migration {filename}: {e}")


def create_initial_migration(app_file: str = 'app.py'):
    """
    Create initial migration for existing models.
    
    Args:
        app_file: Application file
    """
    print("Creating initial migration...")
    
    # Load models
    models = load_app_models(app_file)
    
    if not models:
        print("No models found.")
        return
    
    # Initialize database and migration manager
    db = Database()
    manager = MigrationManager(db)
    
    # Create migration for each model
    for model in models:
        migration_name = f"create_{model.__name__.lower()}_table"
        migration = CreateTableMigration(migration_name, "initial", model)
        manager.add_migration(migration)
    
    # Generate migration file
    migration_file = manager.generate_migration("initial_migration", models)
    print(f"Initial migration created: {migration_file}")


def reset_migrations(app_file: str = 'app.py', confirm: bool = False):
    """
    Reset all migrations (dangerous operation).
    
    Args:
        app_file: Application file
        confirm: Whether to skip confirmation prompt
    """
    if not confirm:
        response = input("This will delete all migration history. Are you sure? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    print("Resetting migrations...")
    
    # Initialize database
    db = Database()
    
    # Drop migrations table
    db.execute("DROP TABLE IF EXISTS wolfpy_migrations")
    db.commit()
    
    print("Migration history reset.")


def squash_migrations(start_migration: str, end_migration: str, name: str):
    """
    Squash multiple migrations into one (advanced feature).
    
    Args:
        start_migration: Starting migration name
        end_migration: Ending migration name
        name: Name for squashed migration
    """
    print(f"Squashing migrations from {start_migration} to {end_migration}...")
    print("Note: This is an advanced feature and should be used with caution.")
    
    # This would require more complex logic to analyze and combine migrations
    # For now, just show a placeholder message
    print("Migration squashing is not yet implemented.")


def check_migrations(app_file: str = 'app.py'):
    """
    Check migration integrity and consistency.
    
    Args:
        app_file: Application file
    """
    print("Checking migration integrity...")
    
    # Initialize database
    db = Database()
    manager = MigrationManager(db)
    
    # Load migration files
    load_migration_files(manager)
    
    # Get applied migrations
    applied = manager.get_applied_migrations()
    
    # Check for issues
    issues = []
    
    # Check if all applied migrations exist in files
    loaded_migrations = {f"{m.name}_{m.version}" for m in manager.migrations}
    for migration in applied:
        migration_key = f"{migration['name']}_{migration['version']}"
        if migration_key not in loaded_migrations:
            issues.append(f"Applied migration not found in files: {migration['name']} ({migration['version']})")
    
    # Check for duplicate versions
    versions = [m.version for m in manager.migrations]
    duplicates = set([v for v in versions if versions.count(v) > 1])
    for version in duplicates:
        issues.append(f"Duplicate migration version: {version}")
    
    if issues:
        print("Migration issues found:")
        for issue in issues:
            print(f"  ⚠ {issue}")
    else:
        print("✓ No migration issues found.")
    
    return len(issues) == 0
