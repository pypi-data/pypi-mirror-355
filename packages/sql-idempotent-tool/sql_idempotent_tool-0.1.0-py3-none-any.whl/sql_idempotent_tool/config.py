"""Configuration management for SQL Idempotent Tool."""

import os
import toml
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class TransformationConfig(BaseModel):
    """Configuration for specific transformation types."""
    enabled: bool = True
    strategy: str = "drop_and_create"  # "drop_and_create", "if_not_exists", "or_replace", "conditional_block", "revoke_and_grant"
    custom_template: Optional[str] = None


class ParserConfig(BaseModel):
    """Configuration for SQL parsing."""
    case_sensitive: bool = False
    ignore_comments: bool = True
    custom_patterns: Dict[str, str] = Field(default_factory=dict)
    excluded_statement_types: Set[str] = Field(default_factory=set)


class OutputConfig(BaseModel):
    """Configuration for output formatting."""
    preserve_formatting: bool = True
    add_comments: bool = True
    comment_template: str = "-- Idempotent transformation applied by sql-idempotent-tool"
    line_ending: str = "\n"
    format_sql: bool = True  # Use SQLFluff to format the output
    sqlfluff_dialect: str = "postgres"  # SQLFluff dialect
    sqlfluff_config_path: Optional[str] = None  # Path to SQLFluff config file


class DatabaseConfig(BaseModel):
    """Database-specific configuration."""
    engine: str = "postgresql"  # postgresql, mysql, sqlite, etc.
    version: str = "15"  # Database version
    use_modern_syntax: bool = True  # Use modern idempotent features when available
    safe_mode: bool = True  # Use conditional blocks instead of DROP + CREATE to preserve dependencies


class SQLIdempotentConfig(BaseModel):
    """Main configuration for SQL Idempotent Tool."""
    
    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    
    # Transformation settings
    transformations: Dict[str, TransformationConfig] = Field(default_factory=lambda: {
        'CREATE_VIEW': TransformationConfig(strategy="or_replace"),
        'CREATE_MATERIALIZED_VIEW': TransformationConfig(strategy="or_replace"),  # PostgreSQL 15+
        'CREATE_TRIGGER': TransformationConfig(strategy="or_replace"),  # PostgreSQL 14+
        'CREATE_TYPE': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 9.1+
        'CREATE_INDEX': TransformationConfig(strategy="if_not_exists"),
        'CREATE_PROCEDURE': TransformationConfig(strategy="or_replace"),  # PostgreSQL 11+
        'CREATE_FUNCTION': TransformationConfig(strategy="or_replace"),
        'CREATE_SCHEMA': TransformationConfig(strategy="if_not_exists"),
        'CREATE_POLICY': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 15+
        'CREATE_SEQUENCE': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 10+
        'CREATE_DOMAIN': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 11+
        'CREATE_EXTENSION': TransformationConfig(strategy="if_not_exists"),
        'CREATE_ROLE': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 8.1+
        'CREATE_USER': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 8.1+
        'GRANT': TransformationConfig(strategy="revoke_and_grant"),
        'ADD_CONSTRAINT': TransformationConfig(strategy="if_not_exists"),  # PostgreSQL 9.6+
    })
    
    # Parser settings
    parser: ParserConfig = Field(default_factory=ParserConfig)
    
    # Output settings
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # File patterns
    include_patterns: List[str] = Field(default_factory=lambda: ["*.sql"])
    exclude_patterns: List[str] = Field(default_factory=lambda: ["*_backup.sql", "*.bak"])
    
    # Safety settings
    require_confirmation: bool = False
    max_file_size_mb: int = 100
    create_backups: bool = True
    backup_suffix: str = ".backup"


def load_config(config_path: Optional[Path] = None) -> SQLIdempotentConfig:
    """Load configuration from file or use defaults."""
    if config_path is None:
        # Look for config in common locations
        possible_paths = [
            Path.cwd() / "sql-idempotent.toml",
            Path.cwd() / ".sql-idempotent.toml",
            Path.home() / ".config" / "sql-idempotent" / "config.toml",
            Path.home() / ".sql-idempotent.toml",
        ]
        
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
    
    if config_path and config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config_data = toml.load(f)
            return SQLIdempotentConfig(**config_data)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            print("Using default configuration.")
    
    return SQLIdempotentConfig()


def save_config(config: SQLIdempotentConfig, config_path: Path) -> None:
    """Save configuration to file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        toml.dump(config.model_dump(), f)


def create_default_config_file(config_path: Path) -> None:
    """Create a default configuration file."""
    config = SQLIdempotentConfig()
    save_config(config, config_path)
    print(f"Created default configuration file at {config_path}")


class ConfigurableTransformer:
    """Enhanced transformer that uses configuration."""
    
    def __init__(self, config: SQLIdempotentConfig):
        self.config = config
    
    def should_transform(self, stmt_type: str) -> bool:
        """Check if a statement type should be transformed based on config."""
        if stmt_type in self.config.transformations:
            return self.config.transformations[stmt_type].enabled
        return True  # Default to enabled for unknown types
    
    def get_transformation_strategy(self, stmt_type: str) -> str:
        """Get the transformation strategy for a statement type."""
        if stmt_type in self.config.transformations:
            return self.config.transformations[stmt_type].strategy
        return "drop_and_create"  # Default strategy
    
    def get_custom_template(self, stmt_type: str) -> Optional[str]:
        """Get custom template for a statement type."""
        if stmt_type in self.config.transformations:
            return self.config.transformations[stmt_type].custom_template
        return None
    
    def add_transformation_comment(self, transformed_sql: str, stmt_type: str) -> str:
        """Add a comment to the transformed SQL if configured."""
        if not self.config.output.add_comments:
            return transformed_sql
        
        comment = self.config.output.comment_template
        if "{stmt_type}" in comment:
            comment = comment.replace("{stmt_type}", stmt_type)
        
        return f"{comment}\n{transformed_sql}"