"""SQL parser using tree-sitter to identify and transform non-idempotent statements."""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import tree_sitter
from tree_sitter import Language, Parser
import logging

logger = logging.getLogger(__name__)


class SQLParser:
    """Parser for SQL files using tree-sitter."""

    def __init__(self):
        """Initialize the SQL parser."""
        try:
            # Try to load the SQL language
            import tree_sitter_sql
            self.sql_language = Language(tree_sitter_sql.language())
            self.parser = Parser(self.sql_language)
        except (ImportError, ValueError) as e:
            # Fallback to regex-based parsing if tree-sitter-sql is not available or incompatible
            print(f"Warning: Tree-sitter SQL parser not available ({e}), falling back to regex parsing")
            self.sql_language = None
            self.parser = None

    def parse_sql(self, sql_content: str) -> List[Dict[str, Any]]:
        """Parse SQL content and return list of statements."""
        if self.parser:
            return self._parse_with_tree_sitter(sql_content)
        else:
            return self._parse_with_regex(sql_content)

    def _parse_with_tree_sitter(self, sql_content: str) -> List[Dict[str, Any]]:
        """Parse SQL using tree-sitter."""
        tree = self.parser.parse(bytes(sql_content, "utf8"))
        statements = []
        
        def traverse_tree(node, depth=0):
            """Traverse the AST and extract relevant statements."""
            if node.type in ['create_view_statement', 'create_trigger_statement', 
                           'create_type_statement', 'create_index_statement',
                           'create_procedure_statement', 'create_function_statement',
                           'create_schema_statement', 'create_policy_statement',
                           'alter_table_statement']:
                
                statement_text = sql_content[node.start_byte:node.end_byte]
                statement_info = {
                    'type': self._get_statement_type(node.type, statement_text),
                    'text': statement_text,
                    'start_byte': node.start_byte,
                    'end_byte': node.end_byte,
                    'name': self._extract_name_from_node(node, sql_content)
                }
                statements.append(statement_info)
            
            for child in node.children:
                traverse_tree(child, depth + 1)
        
        traverse_tree(tree.root_node)
        return statements

    def _parse_with_regex(self, sql_content: str) -> List[Dict[str, Any]]:
        """Fallback regex-based parsing."""
        statements = []
        
        # Patterns for different statement types
        patterns = {
            'CREATE_VIEW': r'CREATE\s+VIEW\s+(\w+)',
            'CREATE_MATERIALIZED_VIEW': r'CREATE\s+MATERIALIZED\s+VIEW\s+(\w+)',
            'CREATE_TRIGGER': r'CREATE\s+TRIGGER\s+(\w+)',
            'CREATE_TYPE': r'CREATE\s+TYPE\s+(\w+)',
            'CREATE_INDEX': r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)',
            'CREATE_PROCEDURE': r'CREATE\s+PROCEDURE\s+(\w+)',
            'CREATE_FUNCTION': r'CREATE\s+FUNCTION\s+(\w+)',
            'CREATE_SCHEMA': r'CREATE\s+SCHEMA\s+(\w+)',
            'CREATE_POLICY': r'CREATE\s+POLICY\s+(\w+)\s+ON\s+(\w+)',
            'CREATE_SEQUENCE': r'CREATE\s+SEQUENCE\s+(\w+)',
            'CREATE_DOMAIN': r'CREATE\s+DOMAIN\s+(\w+)',
            'CREATE_EXTENSION': r'CREATE\s+EXTENSION\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?(\w+(?:-\w+)*)["\']?',
            'CREATE_ROLE': r'CREATE\s+ROLE\s+(\w+)',
            'CREATE_USER': r'CREATE\s+USER\s+(\w+)',
            'GRANT': r'GRANT\s+.+?\s+TO\s+(\w+)',
            'ADD_CONSTRAINT': r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+CONSTRAINT\s+(\w+)',
        }
        
        for stmt_type, pattern in patterns.items():
            for match in re.finditer(pattern, sql_content, re.IGNORECASE | re.MULTILINE):
                # Find the full statement by looking for the next semicolon
                start_pos = match.start()
                end_pos = sql_content.find(';', start_pos)
                if end_pos == -1:
                    end_pos = len(sql_content)
                else:
                    end_pos += 1  # Include the semicolon
                
                statement_text = sql_content[start_pos:end_pos].strip()
                
                # Handle different statement types with different group arrangements
                if stmt_type == 'ADD_CONSTRAINT':
                    # For ADD CONSTRAINT: group 1 = table_name, group 2 = constraint_name
                    name = match.group(2) if len(match.groups()) > 1 else ''
                    table_name = match.group(1) if match.groups() else None
                elif stmt_type == 'CREATE_POLICY':
                    # For CREATE POLICY: group 1 = policy_name, group 2 = table_name
                    name = match.group(1) if match.groups() else ''
                    table_name = match.group(2) if len(match.groups()) > 1 else None
                elif stmt_type == 'GRANT':
                    # For GRANT: extract user/role name and table/object name
                    name = match.group(1) if match.groups() else ''
                    # Extract table/object name from the statement
                    grant_match = re.search(r'GRANT\s+.+?\s+ON\s+(\w+)\s+TO', statement_text, re.IGNORECASE)
                    table_name = grant_match.group(1) if grant_match else None
                else:
                    # For other statements: group 1 = name
                    name = match.group(1) if match.groups() else ''
                    table_name = None
                
                statement_info = {
                    'type': stmt_type,
                    'text': statement_text,
                    'start_byte': start_pos,
                    'end_byte': end_pos,
                    'name': name,
                    'table_name': table_name
                }
                statements.append(statement_info)
        
        return statements

    def _get_statement_type(self, node_type: str, statement_text: str) -> str:
        """Convert tree-sitter node type to our statement type."""
        type_mapping = {
            'create_view_statement': 'CREATE_VIEW',
            'create_trigger_statement': 'CREATE_TRIGGER',
            'create_type_statement': 'CREATE_TYPE',
            'create_index_statement': 'CREATE_INDEX',
            'create_procedure_statement': 'CREATE_PROCEDURE',
            'create_function_statement': 'CREATE_FUNCTION',
            'create_schema_statement': 'CREATE_SCHEMA',
            'create_policy_statement': 'CREATE_POLICY',
        }
        
        if node_type == 'alter_table_statement' and 'ADD CONSTRAINT' in statement_text.upper():
            return 'ADD_CONSTRAINT'
        
        return type_mapping.get(node_type, 'UNKNOWN')

    def _extract_name_from_node(self, node, sql_content: str) -> str:
        """Extract the name from a tree-sitter node."""
        # This is a simplified implementation
        # In a real implementation, you'd traverse the node to find the identifier
        statement_text = sql_content[node.start_byte:node.end_byte]
        
        # Use regex as fallback for name extraction
        patterns = {
            'CREATE_VIEW': r'CREATE\s+VIEW\s+(\w+)',
            'CREATE_TRIGGER': r'CREATE\s+TRIGGER\s+(\w+)',
            'CREATE_TYPE': r'CREATE\s+TYPE\s+(\w+)',
            'CREATE_INDEX': r'CREATE\s+(?:UNIQUE\s+)?INDEX\s+(\w+)',
            'CREATE_PROCEDURE': r'CREATE\s+PROCEDURE\s+(\w+)',
            'CREATE_FUNCTION': r'CREATE\s+FUNCTION\s+(\w+)',
            'CREATE_SCHEMA': r'CREATE\s+SCHEMA\s+(\w+)',
            'CREATE_POLICY': r'CREATE\s+POLICY\s+(\w+)',
            'ADD_CONSTRAINT': r'ADD\s+CONSTRAINT\s+(\w+)',
        }
        
        for pattern in patterns.values():
            match = re.search(pattern, statement_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ''

    def find_non_idempotent_statements(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find statements that are not idempotent."""
        non_idempotent = []
        
        for stmt in statements:
            if self._is_non_idempotent(stmt):
                non_idempotent.append(stmt)
        
        return non_idempotent

    def _is_non_idempotent(self, statement: Dict[str, Any]) -> bool:
        """Check if a statement is non-idempotent."""
        stmt_text = statement['text'].upper()
        stmt_type = statement['type']
        
        # Check if already idempotent
        if 'OR REPLACE' in stmt_text:
            return False
        if 'IF NOT EXISTS' in stmt_text:
            return False
        if 'IF EXISTS' in stmt_text:
            return False
        
        # These statement types need idempotent handling
        idempotent_types = {
            'CREATE_VIEW', 'CREATE_MATERIALIZED_VIEW', 'CREATE_TRIGGER', 'CREATE_TYPE', 
            'CREATE_INDEX', 'CREATE_PROCEDURE', 'CREATE_FUNCTION', 'CREATE_SCHEMA',
            'CREATE_POLICY', 'CREATE_SEQUENCE', 'CREATE_DOMAIN', 'CREATE_EXTENSION',
            'CREATE_ROLE', 'CREATE_USER', 'GRANT', 'ADD_CONSTRAINT'
        }
        
        return stmt_type in idempotent_types


class IdempotentTransformer:
    """Transform SQL statements to be idempotent."""
    
    def __init__(self, db_engine="postgresql", db_version="15", use_modern_syntax=True, config=None):
        self.db_engine = db_engine.lower()
        self.db_version = self._parse_version(db_version)
        self.use_modern_syntax = use_modern_syntax
        self.config = config
        
        # Initialize formatter if enabled
        self.formatter = None
        if config and config.output.format_sql:
            try:
                from .formatter import SQLFormatter
                sqlfluff_config_path = None
                if config.output.sqlfluff_config_path:
                    sqlfluff_config_path = Path(config.output.sqlfluff_config_path)
                
                self.formatter = SQLFormatter(
                    dialect=config.output.sqlfluff_dialect,
                    config_path=sqlfluff_config_path
                )
                
                if not self.formatter.is_available():
                    logger.warning("SQLFluff is not available, formatting will be skipped")
                    self.formatter = None
            except ImportError:
                logger.warning("SQLFluff formatter not available")
                self.formatter = None
    
    def _parse_version(self, version_str):
        """Parse version string to tuple for comparison."""
        try:
            parts = version_str.split('.')
            return tuple(int(part) for part in parts)
        except:
            return (15, 0)  # Default to PostgreSQL 15
    
    def _supports_feature(self, feature_name, min_version):
        """Check if the database version supports a specific feature."""
        if not self.use_modern_syntax:
            return False
        
        if self.db_engine != "postgresql":
            return False  # For now, only PostgreSQL modern features
        
        return self.db_version >= self._parse_version(min_version)

    def transform_sql_file(self, sql_content: str) -> str:
        """Transform an entire SQL file to make statements idempotent."""
        parser = SQLParser()
        statements = parser.parse_sql(sql_content)
        non_idempotent = parser.find_non_idempotent_statements(statements)
        
        # Sort by start position in reverse order to avoid offset issues
        non_idempotent.sort(key=lambda x: x['start_byte'], reverse=True)
        
        result = sql_content
        
        for stmt in non_idempotent:
            original_text = stmt['text']
            transformed_text = self._transform_statement(stmt)
            
            # Replace the original statement with the transformed one
            result = (result[:stmt['start_byte']] + 
                     transformed_text + 
                     result[stmt['end_byte']:])
        
        return result

    def _transform_statement(self, statement: Dict[str, Any]) -> str:
        """Transform a single statement based on its type."""
        stmt_type = statement['type']
        stmt_text = statement['text']
        stmt_name = statement['name']
        table_name = statement.get('table_name')
        
        transformers = {
            'CREATE_VIEW': lambda: self.transform_create_view(stmt_text),
            'CREATE_MATERIALIZED_VIEW': lambda: self.transform_create_materialized_view(stmt_text, stmt_name),
            'CREATE_TRIGGER': lambda: self.transform_create_trigger(stmt_text, stmt_name),
            'CREATE_TYPE': lambda: self.transform_create_type(stmt_text, stmt_name),
            'CREATE_INDEX': lambda: self.transform_create_index(stmt_text),
            'CREATE_PROCEDURE': lambda: self.transform_create_procedure(stmt_text, stmt_name),
            'CREATE_FUNCTION': lambda: self.transform_create_function(stmt_text),
            'CREATE_SCHEMA': lambda: self.transform_create_schema(stmt_text),
            'CREATE_POLICY': lambda: self.transform_create_policy(stmt_text, stmt_name, table_name),
            'CREATE_SEQUENCE': lambda: self.transform_create_sequence(stmt_text, stmt_name),
            'CREATE_DOMAIN': lambda: self.transform_create_domain(stmt_text, stmt_name),
            'CREATE_EXTENSION': lambda: self.transform_create_extension(stmt_text),
            'CREATE_ROLE': lambda: self.transform_create_role(stmt_text, stmt_name),
            'CREATE_USER': lambda: self.transform_create_user(stmt_text, stmt_name),
            'GRANT': lambda: self.transform_grant(stmt_text, stmt_name, table_name),
            'ADD_CONSTRAINT': lambda: self.transform_add_constraint(stmt_text, stmt_name, table_name),
        }
        
        transformer = transformers.get(stmt_type)
        if transformer:
            return transformer()
        
        return stmt_text

    def transform_create_view(self, statement: str) -> str:
        """Transform CREATE VIEW to be idempotent."""
        if self.config and self.config.database.safe_mode:
            # Extract view name for conditional block
            view_match = re.search(r'CREATE\s+VIEW\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:(\w+)\.)?(\w+)', statement, re.IGNORECASE)
            if view_match:
                schema_name = view_match.group(1)
                view_name = view_match.group(2)
                return self._generate_conditional_block(statement, 'VIEW', view_name, schema_name)
        
        return re.sub(r'CREATE\s+VIEW', 'CREATE OR REPLACE VIEW', statement, flags=re.IGNORECASE)

    def transform_create_trigger(self, statement: str, trigger_name: str) -> str:
        """Transform CREATE TRIGGER to be idempotent."""
        if self.config and self.config.database.safe_mode:
            return self._generate_conditional_block(statement, 'TRIGGER', trigger_name)
        
        # PostgreSQL 14+ supports CREATE OR REPLACE TRIGGER
        if self._supports_feature("or_replace_trigger", "14"):
            return re.sub(r'CREATE\s+TRIGGER', 'CREATE OR REPLACE TRIGGER', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP TRIGGER IF EXISTS {trigger_name};\n"
            return drop_statement + statement

    def transform_create_type(self, statement: str, type_name: str) -> str:
        """Transform CREATE TYPE to be idempotent."""
        if self.config and self.config.database.safe_mode:
            return self._generate_conditional_block(statement, 'TYPE', type_name)
        
        # PostgreSQL 9.1+ supports CREATE TYPE IF NOT EXISTS for some types
        if self._supports_feature("type_if_not_exists", "9.1"):
            # For ENUM types, we can use IF NOT EXISTS
            if "AS ENUM" in statement.upper():
                return re.sub(r'CREATE\s+TYPE\s+(\w+)', r'CREATE TYPE IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        
        # Fallback to DROP + CREATE
        drop_statement = f"DROP TYPE IF EXISTS {type_name};\n"
        return drop_statement + statement

    def transform_create_index(self, statement: str) -> str:
        """Transform CREATE INDEX to CREATE INDEX IF NOT EXISTS."""
        # Handle both regular and unique indexes
        return re.sub(r'CREATE\s+((?:UNIQUE\s+)?INDEX)', r'CREATE \1 IF NOT EXISTS', statement, flags=re.IGNORECASE)

    def transform_create_procedure(self, statement: str, procedure_name: str) -> str:
        """Transform CREATE PROCEDURE to be idempotent."""
        # PostgreSQL 11+ supports CREATE OR REPLACE PROCEDURE
        if self._supports_feature("or_replace_procedure", "11"):
            return re.sub(r'CREATE\s+PROCEDURE', 'CREATE OR REPLACE PROCEDURE', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP PROCEDURE IF EXISTS {procedure_name};\n"
            return drop_statement + statement

    def transform_create_function(self, statement: str) -> str:
        """Transform CREATE FUNCTION to CREATE OR REPLACE FUNCTION."""
        return re.sub(r'CREATE\s+FUNCTION', 'CREATE OR REPLACE FUNCTION', statement, flags=re.IGNORECASE)

    def transform_create_schema(self, statement: str) -> str:
        """Transform CREATE SCHEMA to CREATE SCHEMA IF NOT EXISTS."""
        return re.sub(r'CREATE\s+SCHEMA', 'CREATE SCHEMA IF NOT EXISTS', statement, flags=re.IGNORECASE)

    def transform_create_policy(self, statement: str, policy_name: str, table_name: Optional[str]) -> str:
        """Transform CREATE POLICY to be idempotent."""
        # PostgreSQL 15+ supports CREATE POLICY IF NOT EXISTS
        if self._supports_feature("policy_if_not_exists", "15"):
            return re.sub(r'CREATE\s+POLICY\s+(\w+)', r'CREATE POLICY IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            if table_name:
                drop_statement = f"DROP POLICY IF EXISTS {policy_name} ON {table_name};\n"
            else:
                # Extract table name from statement if not provided
                match = re.search(r'ON\s+(\w+)', statement, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
                    drop_statement = f"DROP POLICY IF EXISTS {policy_name} ON {table_name};\n"
                else:
                    drop_statement = f"-- Could not determine table name for policy {policy_name}\n"
            
            return drop_statement + statement

    def transform_add_constraint(self, statement: str, constraint_name: str, table_name: Optional[str]) -> str:
        """Transform ADD CONSTRAINT to be idempotent."""
        # PostgreSQL 9.6+ supports ADD CONSTRAINT IF NOT EXISTS
        if self._supports_feature("constraint_if_not_exists", "9.6"):
            return re.sub(r'ADD\s+CONSTRAINT\s+(\w+)', r'ADD CONSTRAINT IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + ADD for older versions
            if not table_name:
                # Extract table name from statement
                match = re.search(r'ALTER\s+TABLE\s+(\w+)', statement, re.IGNORECASE)
                if match:
                    table_name = match.group(1)
            
            if table_name:
                drop_statement = f"ALTER TABLE {table_name} DROP CONSTRAINT IF EXISTS {constraint_name};\n"
            else:
                drop_statement = f"-- Could not determine table name for constraint {constraint_name}\n"
            
            return drop_statement + statement

    def transform_create_materialized_view(self, statement: str, view_name: str) -> str:
        """Transform CREATE MATERIALIZED VIEW to be idempotent."""
        # PostgreSQL 15+ supports CREATE OR REPLACE MATERIALIZED VIEW
        if self._supports_feature("or_replace_materialized_view", "15"):
            return re.sub(r'CREATE\s+MATERIALIZED\s+VIEW', 'CREATE OR REPLACE MATERIALIZED VIEW', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP MATERIALIZED VIEW IF EXISTS {view_name};\n"
            return drop_statement + statement

    def transform_create_sequence(self, statement: str, sequence_name: str) -> str:
        """Transform CREATE SEQUENCE to be idempotent."""
        # PostgreSQL 10+ supports CREATE SEQUENCE IF NOT EXISTS
        if self._supports_feature("sequence_if_not_exists", "10"):
            return re.sub(r'CREATE\s+SEQUENCE\s+(\w+)', r'CREATE SEQUENCE IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP SEQUENCE IF EXISTS {sequence_name};\n"
            return drop_statement + statement

    def transform_create_domain(self, statement: str, domain_name: str) -> str:
        """Transform CREATE DOMAIN to be idempotent."""
        # PostgreSQL 11+ supports CREATE DOMAIN IF NOT EXISTS
        if self._supports_feature("domain_if_not_exists", "11"):
            return re.sub(r'CREATE\s+DOMAIN\s+(\w+)', r'CREATE DOMAIN IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP DOMAIN IF EXISTS {domain_name};\n"
            return drop_statement + statement

    def transform_create_extension(self, statement: str) -> str:
        """Transform CREATE EXTENSION to CREATE EXTENSION IF NOT EXISTS."""
        return re.sub(r'CREATE\s+EXTENSION\s+', 'CREATE EXTENSION IF NOT EXISTS ', statement, flags=re.IGNORECASE)

    def transform_create_role(self, statement: str, role_name: str) -> str:
        """Transform CREATE ROLE to be idempotent."""
        # PostgreSQL 8.1+ supports CREATE ROLE IF NOT EXISTS
        if self._supports_feature("role_if_not_exists", "8.1"):
            return re.sub(r'CREATE\s+ROLE\s+(\w+)', r'CREATE ROLE IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP ROLE IF EXISTS {role_name};\n"
            return drop_statement + statement

    def transform_create_user(self, statement: str, user_name: str) -> str:
        """Transform CREATE USER to be idempotent."""
        # PostgreSQL 8.1+ supports CREATE USER IF NOT EXISTS
        if self._supports_feature("user_if_not_exists", "8.1"):
            return re.sub(r'CREATE\s+USER\s+(\w+)', r'CREATE USER IF NOT EXISTS \1', statement, flags=re.IGNORECASE)
        else:
            # Fallback to DROP + CREATE for older versions
            drop_statement = f"DROP USER IF EXISTS {user_name};\n"
            return drop_statement + statement

    def transform_grant(self, statement: str, user_name: str, table_name: Optional[str]) -> str:
        """Transform GRANT to include REVOKE."""
        if table_name:
            revoke_statement = f"REVOKE ALL ON {table_name} FROM {user_name};\n"
        else:
            # Extract object name from statement if not provided
            grant_match = re.search(r'GRANT\s+.+?\s+ON\s+(\w+)\s+TO', statement, re.IGNORECASE)
            if grant_match:
                object_name = grant_match.group(1)
                revoke_statement = f"REVOKE ALL ON {object_name} FROM {user_name};\n"
            else:
                revoke_statement = f"-- Could not determine object name for GRANT to {user_name}\n"
        
        return revoke_statement + statement

    def _generate_conditional_block(self, statement: str, object_type: str, object_name: str, schema_name: Optional[str] = None) -> str:
        """Generate a DO block that conditionally executes the statement only if the object doesn't exist."""
        
        # Build the full object name with schema if provided
        full_name = f"{schema_name}.{object_name}" if schema_name else object_name
        
        # Define existence checks for different object types
        existence_checks = {
            'VIEW': f"""
                SELECT 1 FROM information_schema.views 
                WHERE table_name = '{object_name}' 
                {f"AND table_schema = '{schema_name}'" if schema_name else "AND table_schema = current_schema()"}
            """,
            'MATERIALIZED_VIEW': f"""
                SELECT 1 FROM pg_matviews 
                WHERE matviewname = '{object_name}' 
                {f"AND schemaname = '{schema_name}'" if schema_name else "AND schemaname = current_schema()"}
            """,
            'TRIGGER': f"""
                SELECT 1 FROM information_schema.triggers 
                WHERE trigger_name = '{object_name}'
            """,
            'TYPE': f"""
                SELECT 1 FROM pg_type t 
                JOIN pg_namespace n ON t.typnamespace = n.oid 
                WHERE t.typname = '{object_name}' 
                {f"AND n.nspname = '{schema_name}'" if schema_name else "AND n.nspname = current_schema()"}
            """,
            'INDEX': f"""
                SELECT 1 FROM pg_indexes 
                WHERE indexname = '{object_name}' 
                {f"AND schemaname = '{schema_name}'" if schema_name else "AND schemaname = current_schema()"}
            """,
            'PROCEDURE': f"""
                SELECT 1 FROM information_schema.routines 
                WHERE routine_name = '{object_name}' 
                AND routine_type = 'PROCEDURE'
                {f"AND routine_schema = '{schema_name}'" if schema_name else "AND routine_schema = current_schema()"}
            """,
            'FUNCTION': f"""
                SELECT 1 FROM information_schema.routines 
                WHERE routine_name = '{object_name}' 
                AND routine_type = 'FUNCTION'
                {f"AND routine_schema = '{schema_name}'" if schema_name else "AND routine_schema = current_schema()"}
            """,
            'SCHEMA': f"""
                SELECT 1 FROM information_schema.schemata 
                WHERE schema_name = '{object_name}'
            """,
            'POLICY': f"""
                SELECT 1 FROM pg_policies 
                WHERE policyname = '{object_name}'
            """,
            'SEQUENCE': f"""
                SELECT 1 FROM information_schema.sequences 
                WHERE sequence_name = '{object_name}' 
                {f"AND sequence_schema = '{schema_name}'" if schema_name else "AND sequence_schema = current_schema()"}
            """,
            'DOMAIN': f"""
                SELECT 1 FROM information_schema.domains 
                WHERE domain_name = '{object_name}' 
                {f"AND domain_schema = '{schema_name}'" if schema_name else "AND domain_schema = current_schema()"}
            """,
            'EXTENSION': f"""
                SELECT 1 FROM pg_extension 
                WHERE extname = '{object_name}'
            """,
            'ROLE': f"""
                SELECT 1 FROM pg_roles 
                WHERE rolname = '{object_name}'
            """,
            'USER': f"""
                SELECT 1 FROM pg_user 
                WHERE usename = '{object_name}'
            """
        }
        
        existence_check = existence_checks.get(object_type, f"SELECT 1 FROM pg_class WHERE relname = '{object_name}'")
        
        # Clean up the statement for embedding in the DO block
        clean_statement = statement.strip()
        if clean_statement.endswith(';'):
            clean_statement = clean_statement[:-1]
        
        # Escape single quotes in the statement
        escaped_statement = clean_statement.replace("'", "''")
        
        return f"""DO $$
BEGIN
    IF NOT EXISTS ({existence_check.strip()}) THEN
        EXECUTE '{escaped_statement}';
    END IF;
END $$;"""

    def _generate_constraint_conditional_block(self, statement: str, constraint_name: str, table_name: str, schema_name: Optional[str] = None) -> str:
        """Generate a DO block that conditionally adds a constraint only if it doesn't exist."""
        
        existence_check = f"""
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = '{constraint_name}' 
            AND table_name = '{table_name}'
            {f"AND table_schema = '{schema_name}'" if schema_name else "AND table_schema = current_schema()"}
        """
        
        # Clean up the statement for embedding in the DO block
        clean_statement = statement.strip()
        if clean_statement.endswith(';'):
            clean_statement = clean_statement[:-1]
        
        # Escape single quotes in the statement
        escaped_statement = clean_statement.replace("'", "''")
        
        return f"""DO $$
BEGIN
    IF NOT EXISTS ({existence_check.strip()}) THEN
        EXECUTE '{escaped_statement}';
    END IF;
END $$;"""
    
    def format_sql(self, sql_content: str) -> str:
        """
        Format SQL content using SQLFluff if available.
        
        Args:
            sql_content: Raw SQL content to format
            
        Returns:
            Formatted SQL content
        """
        if self.formatter:
            try:
                logger.info("Formatting SQL with SQLFluff...")
                formatted = self.formatter.format_sql(sql_content)
                logger.info("SQL formatted using SQLFluff")
                return formatted
            except Exception as e:
                logger.warning(f"SQLFluff formatting failed: {e}")
                return sql_content
        else:
            logger.info("SQLFluff formatter not available, skipping formatting")
            return sql_content
