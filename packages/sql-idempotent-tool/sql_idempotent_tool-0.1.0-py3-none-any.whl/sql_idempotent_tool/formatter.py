"""SQL formatting using SQLFluff."""

import tempfile
from pathlib import Path
from typing import Optional
import subprocess
import logging

logger = logging.getLogger(__name__)


class SQLFormatter:
    """Format SQL code using SQLFluff."""
    
    def __init__(self, dialect: str = "postgres", config_path: Optional[Path] = None):
        """
        Initialize the SQL formatter.
        
        Args:
            dialect: SQL dialect for SQLFluff (postgres, mysql, sqlite, etc.)
            config_path: Optional path to SQLFluff config file
        """
        self.dialect = dialect
        self.config_path = config_path
        
    def format_sql(self, sql_content: str) -> str:
        """
        Format SQL content using SQLFluff.
        
        Args:
            sql_content: Raw SQL content to format
            
        Returns:
            Formatted SQL content
        """
        try:
            # Create a temporary file for the SQL content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(sql_content)
                temp_file_path = temp_file.name
            
            # Build SQLFluff command
            cmd = ['sqlfluff', 'format', '--dialect', self.dialect]
            
            # Add config file if specified
            if self.config_path and self.config_path.exists():
                cmd.extend(['--config', str(self.config_path)])
            
            # Add the temporary file
            cmd.append(temp_file_path)
            
            # Run SQLFluff format
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Read the formatted content
                formatted_content = Path(temp_file_path).read_text()
                
                # Clean up temporary file
                Path(temp_file_path).unlink()
                
                return formatted_content
            else:
                logger.warning(f"SQLFluff formatting failed: {result.stderr}")
                # Clean up temporary file
                Path(temp_file_path).unlink()
                return sql_content
                
        except subprocess.TimeoutExpired:
            logger.warning("SQLFluff formatting timed out")
            return sql_content
        except Exception as e:
            logger.warning(f"SQLFluff formatting error: {e}")
            return sql_content
    
    def lint_sql(self, sql_content: str) -> dict:
        """
        Lint SQL content using SQLFluff.
        
        Args:
            sql_content: SQL content to lint
            
        Returns:
            Dictionary with linting results
        """
        try:
            # Create a temporary file for the SQL content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
                temp_file.write(sql_content)
                temp_file_path = temp_file.name
            
            # Build SQLFluff command
            cmd = ['sqlfluff', 'lint', '--dialect', self.dialect, '--format', 'json']
            
            # Add config file if specified
            if self.config_path and self.config_path.exists():
                cmd.extend(['--config', str(self.config_path)])
            
            # Add the temporary file
            cmd.append(temp_file_path)
            
            # Run SQLFluff lint
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up temporary file
            Path(temp_file_path).unlink()
            
            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                try:
                    import json
                    return json.loads(result.stdout) if result.stdout else {}
                except json.JSONDecodeError:
                    return {"error": "Failed to parse SQLFluff output"}
            else:
                return {"error": f"SQLFluff linting failed: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            return {"error": "SQLFluff linting timed out"}
        except Exception as e:
            return {"error": f"SQLFluff linting error: {e}"}
    
    def is_available(self) -> bool:
        """Check if SQLFluff is available."""
        try:
            result = subprocess.run(
                ['sqlfluff', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


def create_sqlfluff_config(config_path: Path, dialect: str = "postgres") -> None:
    """
    Create a basic SQLFluff configuration file.
    
    Args:
        config_path: Path where to create the config file
        dialect: SQL dialect to configure
    """
    config_content = f"""[sqlfluff]
dialect = {dialect}
templater = jinja
exclude_rules = L003,L014,L016,L031,L034

[sqlfluff:indentation]
indent_unit = space
tab_space_size = 4

[sqlfluff:layout:type:comma]
spacing_before = touch
line_position = trailing

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.identifiers]
capitalisation_policy = lower

[sqlfluff:rules:capitalisation.functions]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.literals]
capitalisation_policy = upper
"""
    
    config_path.write_text(config_content)