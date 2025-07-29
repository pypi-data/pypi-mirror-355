"""
WolfPy Migration System.

Database migration management for WolfPy ORM.
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Type, Any
from .database import Database, Model


class Migration:
    """Base class for database migrations."""
    
    def __init__(self, name: str, version: str):
        """
        Initialize migration.
        
        Args:
            name: Migration name
            version: Migration version (timestamp)
        """
        self.name = name
        self.version = version
        self.dependencies = []
    
    def up(self, db: Database):
        """Apply migration (override in subclasses)."""
        raise NotImplementedError("Migration must implement up() method")
    
    def down(self, db: Database):
        """Reverse migration (override in subclasses)."""
        raise NotImplementedError("Migration must implement down() method")
    
    def get_checksum(self) -> str:
        """Get migration checksum for integrity verification."""
        content = f"{self.name}_{self.version}"
        return hashlib.md5(content.encode()).hexdigest()


class CreateTableMigration(Migration):
    """Migration for creating tables."""
    
    def __init__(self, name: str, version: str, model_class: Type[Model]):
        """
        Initialize create table migration.
        
        Args:
            name: Migration name
            version: Migration version
            model_class: Model class to create table for
        """
        super().__init__(name, version)
        self.model_class = model_class
    
    def up(self, db: Database):
        """Create table."""
        sql = self.model_class.get_create_sql()
        db.execute(sql)
        
        # Create indexes if defined
        if hasattr(self.model_class, '_indexes'):
            for index in self.model_class._indexes:
                self._create_index(db, index)
    
    def down(self, db: Database):
        """Drop table."""
        table_name = self.model_class.get_table_name()
        sql = f"DROP TABLE IF EXISTS {table_name}"
        db.execute(sql)
    
    def _create_index(self, db: Database, index_config: Dict[str, Any]):
        """Create index based on configuration."""
        table_name = self.model_class.get_table_name()
        columns = index_config.get('columns', [])
        unique = index_config.get('unique', False)
        
        if columns:
            index_name = f"idx_{table_name}_{'_'.join(columns)}"
            unique_sql = "UNIQUE " if unique else ""
            columns_sql = ', '.join(columns)
            sql = f"CREATE {unique_sql}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_sql})"
            db.execute(sql)


class AddColumnMigration(Migration):
    """Migration for adding columns."""
    
    def __init__(self, name: str, version: str, table_name: str, column_name: str, column_type: str):
        """
        Initialize add column migration.
        
        Args:
            name: Migration name
            version: Migration version
            table_name: Target table name
            column_name: Column name to add
            column_type: Column type definition
        """
        super().__init__(name, version)
        self.table_name = table_name
        self.column_name = column_name
        self.column_type = column_type
    
    def up(self, db: Database):
        """Add column."""
        sql = f"ALTER TABLE {self.table_name} ADD COLUMN {self.column_name} {self.column_type}"
        db.execute(sql)
    
    def down(self, db: Database):
        """Remove column (SQLite doesn't support DROP COLUMN directly)."""
        # For SQLite, we need to recreate the table without the column
        # This is a simplified implementation
        print(f"Warning: Cannot drop column {self.column_name} from {self.table_name} in SQLite")


class DropColumnMigration(Migration):
    """Migration for dropping columns."""
    
    def __init__(self, name: str, version: str, table_name: str, column_name: str):
        """
        Initialize drop column migration.
        
        Args:
            name: Migration name
            version: Migration version
            table_name: Target table name
            column_name: Column name to drop
        """
        super().__init__(name, version)
        self.table_name = table_name
        self.column_name = column_name
    
    def up(self, db: Database):
        """Drop column (SQLite doesn't support DROP COLUMN directly)."""
        print(f"Warning: Cannot drop column {self.column_name} from {self.table_name} in SQLite")
    
    def down(self, db: Database):
        """Add column back."""
        # This would need the original column definition
        print(f"Warning: Cannot restore column {self.column_name} to {self.table_name}")


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db: Database, migrations_dir: str = "migrations"):
        """
        Initialize migration manager.
        
        Args:
            db: Database instance
            migrations_dir: Directory containing migration files
        """
        self.db = db
        self.migrations_dir = migrations_dir
        self.migrations = []
        self._ensure_migrations_table()
    
    def _ensure_migrations_table(self):
        """Create migrations tracking table if it doesn't exist."""
        sql = """
        CREATE TABLE IF NOT EXISTS wolfpy_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            version VARCHAR(20) NOT NULL,
            checksum VARCHAR(32) NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, version)
        )
        """
        self.db.execute(sql)
        self.db.commit()
    
    def add_migration(self, migration: Migration):
        """Add migration to the list."""
        self.migrations.append(migration)
    
    def generate_migration(self, name: str, model_classes: List[Type[Model]] = None) -> str:
        """
        Generate migration file.
        
        Args:
            name: Migration name
            model_classes: List of model classes to include
            
        Returns:
            Generated migration file path
        """
        # Create migrations directory if it doesn't exist
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Generate version timestamp
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate migration file name
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())
        filename = f"{version}_{safe_name}.py"
        filepath = os.path.join(self.migrations_dir, filename)
        
        # Generate migration content
        content = self._generate_migration_content(name, version, model_classes)
        
        # Write migration file
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"Generated migration: {filepath}")
        return filepath
    
    def _generate_migration_content(self, name: str, version: str, model_classes: List[Type[Model]] = None) -> str:
        """Generate migration file content."""
        content = f'''"""
Migration: {name}
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from wolfpy.core.migrations import Migration
from wolfpy.core.database import Database


class {name.replace(' ', '').replace('_', '')}Migration(Migration):
    """Migration for {name}."""
    
    def __init__(self):
        super().__init__("{name}", "{version}")
    
    def up(self, db: Database):
        """Apply migration."""
'''
        
        if model_classes:
            for model_class in model_classes:
                table_sql = model_class.get_create_sql()
                content += f'        # Create table for {model_class.__name__}\n'
                content += f'        db.execute("""{table_sql}""")\n'
        else:
            content += '        # Add your migration code here\n'
            content += '        pass\n'
        
        content += '''
    def down(self, db: Database):
        """Reverse migration."""
        # Add rollback code here
        pass


# Migration instance
migration = ''' + name.replace(' ', '').replace('_', '') + '''Migration()
'''
        
        return content
    
    def get_applied_migrations(self) -> List[Dict[str, Any]]:
        """Get list of applied migrations."""
        sql = "SELECT name, version, checksum, applied_at FROM wolfpy_migrations ORDER BY applied_at"
        rows = self.db.fetchall(sql)
        return [
            {
                'name': row[0],
                'version': row[1], 
                'checksum': row[2],
                'applied_at': row[3]
            }
            for row in rows
        ]
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        applied = {f"{m['name']}_{m['version']}" for m in self.get_applied_migrations()}
        return [m for m in self.migrations if f"{m.name}_{m.version}" not in applied]
    
    def apply_migration(self, migration: Migration):
        """Apply a single migration."""
        try:
            with self.db.transaction():
                # Apply migration
                migration.up(self.db)
                
                # Record migration
                sql = """
                INSERT INTO wolfpy_migrations (name, version, checksum)
                VALUES (?, ?, ?)
                """
                self.db.execute(sql, (migration.name, migration.version, migration.get_checksum()))
                
                print(f"Applied migration: {migration.name} ({migration.version})")
        
        except Exception as e:
            print(f"Failed to apply migration {migration.name}: {e}")
            raise
    
    def rollback_migration(self, migration: Migration):
        """Rollback a single migration."""
        try:
            with self.db.transaction():
                # Rollback migration
                migration.down(self.db)
                
                # Remove migration record
                sql = "DELETE FROM wolfpy_migrations WHERE name = ? AND version = ?"
                self.db.execute(sql, (migration.name, migration.version))
                
                print(f"Rolled back migration: {migration.name} ({migration.version})")
        
        except Exception as e:
            print(f"Failed to rollback migration {migration.name}: {e}")
            raise
    
    def migrate(self):
        """Apply all pending migrations."""
        pending = self.get_pending_migrations()
        
        if not pending:
            print("No pending migrations.")
            return
        
        print(f"Applying {len(pending)} migrations...")
        
        for migration in pending:
            self.apply_migration(migration)
        
        print("All migrations applied successfully.")
    
    def rollback(self, steps: int = 1):
        """Rollback specified number of migrations."""
        applied = self.get_applied_migrations()
        
        if not applied:
            print("No migrations to rollback.")
            return
        
        # Get migrations to rollback (most recent first)
        to_rollback = applied[-steps:] if steps <= len(applied) else applied
        to_rollback.reverse()
        
        print(f"Rolling back {len(to_rollback)} migrations...")
        
        for migration_info in to_rollback:
            # Find migration object
            migration = None
            for m in self.migrations:
                if m.name == migration_info['name'] and m.version == migration_info['version']:
                    migration = m
                    break
            
            if migration:
                self.rollback_migration(migration)
            else:
                print(f"Warning: Migration {migration_info['name']} not found in loaded migrations")
        
        print("Rollback completed.")
    
    def status(self):
        """Show migration status."""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()
        
        print(f"Applied migrations: {len(applied)}")
        for migration in applied:
            print(f"  ✓ {migration['name']} ({migration['version']})")
        
        print(f"\nPending migrations: {len(pending)}")
        for migration in pending:
            print(f"  ○ {migration.name} ({migration.version})")
        
        if not pending:
            print("  (none)")
