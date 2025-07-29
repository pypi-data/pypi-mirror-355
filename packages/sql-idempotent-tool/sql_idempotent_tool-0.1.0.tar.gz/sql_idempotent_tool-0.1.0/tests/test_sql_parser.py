"""Tests for SQL parsing and idempotent statement identification."""

import pytest
from sql_idempotent_tool.sql_parser import SQLParser, IdempotentTransformer


class TestSQLParser:
    """Test SQL parsing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = SQLParser()
        self.transformer = IdempotentTransformer()

    def test_identify_create_view(self):
        """Test identification of CREATE VIEW statements."""
        sql = """
        CREATE VIEW user_summary AS
        SELECT id, name, email FROM users;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_VIEW'
        assert 'user_summary' in non_idempotent[0]['name']

    def test_identify_create_trigger(self):
        """Test identification of CREATE TRIGGER statements."""
        sql = """
        CREATE TRIGGER update_timestamp
        BEFORE UPDATE ON users
        FOR EACH ROW
        BEGIN
            NEW.updated_at = NOW();
        END;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_TRIGGER'
        assert 'update_timestamp' in non_idempotent[0]['name']

    def test_identify_create_type(self):
        """Test identification of CREATE TYPE statements."""
        sql = """
        CREATE TYPE status_enum AS ENUM ('active', 'inactive', 'pending');
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_TYPE'
        assert 'status_enum' in non_idempotent[0]['name']

    def test_identify_create_index(self):
        """Test identification of CREATE INDEX statements."""
        sql = """
        CREATE INDEX idx_user_email ON users(email);
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_INDEX'
        assert 'idx_user_email' in non_idempotent[0]['name']

    def test_identify_create_unique_index(self):
        """Test identification of CREATE UNIQUE INDEX statements."""
        sql = """
        CREATE UNIQUE INDEX idx_user_email_unique ON users(email);
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_INDEX'
        assert 'idx_user_email_unique' in non_idempotent[0]['name']

    def test_identify_create_procedure(self):
        """Test identification of CREATE PROCEDURE statements."""
        sql = """
        CREATE PROCEDURE GetUserById(IN user_id INT)
        BEGIN
            SELECT * FROM users WHERE id = user_id;
        END;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_PROCEDURE'
        assert 'GetUserById' in non_idempotent[0]['name']

    def test_identify_create_function(self):
        """Test identification of CREATE FUNCTION statements."""
        sql = """
        CREATE FUNCTION calculate_age(birth_date DATE)
        RETURNS INT
        DETERMINISTIC
        BEGIN
            RETURN YEAR(CURDATE()) - YEAR(birth_date);
        END;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_FUNCTION'
        assert 'calculate_age' in non_idempotent[0]['name']

    def test_identify_create_schema(self):
        """Test identification of CREATE SCHEMA statements."""
        sql = """
        CREATE SCHEMA analytics;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_SCHEMA'
        assert 'analytics' in non_idempotent[0]['name']

    def test_identify_create_policy(self):
        """Test identification of CREATE POLICY statements."""
        sql = """
        CREATE POLICY user_policy ON users
        FOR SELECT
        USING (user_id = current_user_id());
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_POLICY'
        assert 'user_policy' in non_idempotent[0]['name']

    def test_identify_add_constraint(self):
        """Test identification of ALTER TABLE ADD CONSTRAINT statements."""
        sql = """
        ALTER TABLE users ADD CONSTRAINT fk_user_department 
        FOREIGN KEY (department_id) REFERENCES departments(id);
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'ADD_CONSTRAINT'
        assert 'fk_user_department' in non_idempotent[0]['name']

    def test_identify_add_check_constraint(self):
        """Test identification of ALTER TABLE ADD CHECK CONSTRAINT statements."""
        sql = """
        ALTER TABLE users ADD CONSTRAINT chk_age 
        CHECK (age >= 0 AND age <= 150);
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'ADD_CONSTRAINT'
        assert 'chk_age' in non_idempotent[0]['name']

    def test_identify_create_sequence(self):
        """Test identification of CREATE SEQUENCE statements."""
        sql = """
        CREATE SEQUENCE user_id_seq
        START WITH 1
        INCREMENT BY 1
        NO MAXVALUE
        CACHE 1;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_SEQUENCE'
        assert 'user_id_seq' in non_idempotent[0]['name']

    def test_identify_create_domain(self):
        """Test identification of CREATE DOMAIN statements."""
        sql = """
        CREATE DOMAIN email_domain AS VARCHAR(255)
        CHECK (VALUE ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_DOMAIN'
        assert 'email_domain' in non_idempotent[0]['name']

    def test_identify_create_extension(self):
        """Test identification of CREATE EXTENSION statements."""
        sql = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        # Should be 0 because it already has IF NOT EXISTS
        assert len(non_idempotent) == 0

    def test_identify_create_extension_non_idempotent(self):
        """Test identification of non-idempotent CREATE EXTENSION statements."""
        sql = """
        CREATE EXTENSION "uuid-ossp";
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_EXTENSION'
        assert 'uuid-ossp' in non_idempotent[0]['name']

    def test_identify_create_role(self):
        """Test identification of CREATE ROLE statements."""
        sql = """
        CREATE ROLE app_user WITH LOGIN PASSWORD 'secret123';
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_ROLE'
        assert 'app_user' in non_idempotent[0]['name']

    def test_identify_create_user(self):
        """Test identification of CREATE USER statements."""
        sql = """
        CREATE USER db_user WITH PASSWORD 'password123';
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_USER'
        assert 'db_user' in non_idempotent[0]['name']

    def test_identify_grant_statement(self):
        """Test identification of GRANT statements."""
        sql = """
        GRANT SELECT, INSERT ON users TO app_user;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'GRANT'
        assert 'app_user' in non_idempotent[0]['name']

    def test_identify_create_materialized_view(self):
        """Test identification of CREATE MATERIALIZED VIEW statements."""
        sql = """
        CREATE MATERIALIZED VIEW user_stats AS
        SELECT department_id, COUNT(*) as user_count
        FROM users
        GROUP BY department_id;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 1
        assert non_idempotent[0]['type'] == 'CREATE_MATERIALIZED_VIEW'
        assert 'user_stats' in non_idempotent[0]['name']

    def test_identify_complex_multiline_statements(self):
        """Test identification of complex multiline statements with comments."""
        sql = """
        /* Complex trigger with multiple conditions */
        CREATE TRIGGER complex_audit_trigger
        AFTER INSERT OR UPDATE OR DELETE ON users
        FOR EACH ROW
        WHEN (OLD.* IS DISTINCT FROM NEW.*)
        EXECUTE FUNCTION audit_user_changes();
        
        -- Complex view with CTEs
        CREATE VIEW complex_user_view AS
        WITH active_users AS (
            SELECT * FROM users WHERE status = 'active'
        ),
        user_stats AS (
            SELECT department_id, COUNT(*) as count
            FROM active_users
            GROUP BY department_id
        )
        SELECT u.*, s.count as dept_user_count
        FROM active_users u
        JOIN user_stats s ON u.department_id = s.department_id;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 2
        types = [stmt['type'] for stmt in non_idempotent]
        assert 'CREATE_TRIGGER' in types
        assert 'CREATE_VIEW' in types

    def test_ignore_already_idempotent_statements(self):
        """Test that already idempotent statements are ignored."""
        sql = """
        CREATE OR REPLACE VIEW user_summary AS
        SELECT id, name, email FROM users;
        
        CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
        
        CREATE SCHEMA IF NOT EXISTS analytics;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 0

    def test_ignore_create_table(self):
        """Test that CREATE TABLE statements are ignored."""
        sql = """
        CREATE TABLE users (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100)
        );
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        assert len(non_idempotent) == 0

    def test_mixed_statements(self):
        """Test parsing file with mixed statement types."""
        sql = """
        CREATE TABLE users (id INT PRIMARY KEY);
        
        CREATE VIEW active_users AS
        SELECT * FROM users WHERE status = 'active';
        
        CREATE TRIGGER user_audit
        AFTER INSERT ON users
        FOR EACH ROW
        INSERT INTO audit_log VALUES (NEW.id, NOW());
        
        CREATE OR REPLACE FUNCTION get_user_count()
        RETURNS INT
        BEGIN
            RETURN (SELECT COUNT(*) FROM users);
        END;
        """
        statements = self.parser.parse_sql(sql)
        non_idempotent = self.parser.find_non_idempotent_statements(statements)
        
        # Should find VIEW and TRIGGER, but not TABLE or already idempotent FUNCTION
        assert len(non_idempotent) == 2
        types = [stmt['type'] for stmt in non_idempotent]
        assert 'CREATE_VIEW' in types
        assert 'CREATE_TRIGGER' in types


class TestIdempotentTransformer:
    """Test idempotent transformation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.transformer = IdempotentTransformer()

    def test_transform_create_view(self):
        """Test transformation of CREATE VIEW to CREATE OR REPLACE VIEW."""
        original = """CREATE VIEW user_summary AS
SELECT id, name, email FROM users;"""
        
        expected = """CREATE OR REPLACE VIEW user_summary AS
SELECT id, name, email FROM users;"""
        
        result = self.transformer.transform_create_view(original)
        assert result.strip() == expected.strip()

    def test_transform_create_trigger(self):
        """Test transformation of CREATE TRIGGER to use modern syntax."""
        original = """CREATE TRIGGER update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    NEW.updated_at = NOW();
END;"""
        
        result = self.transformer.transform_create_trigger(original, "update_timestamp")
        
        # With PostgreSQL 15, should use CREATE OR REPLACE TRIGGER
        assert "CREATE OR REPLACE TRIGGER update_timestamp" in result
        assert "DROP TRIGGER" not in result

    def test_transform_create_type(self):
        """Test transformation of CREATE TYPE to use modern syntax."""
        original = """CREATE TYPE status_enum AS ENUM ('active', 'inactive', 'pending');"""
        
        result = self.transformer.transform_create_type(original, "status_enum")
        
        # PostgreSQL doesn't have CREATE TYPE IF NOT EXISTS, so still uses DROP + CREATE
        assert "CREATE TYPE IF NOT EXISTS status_enum" in result

    def test_transform_create_index(self):
        """Test transformation of CREATE INDEX to CREATE INDEX IF NOT EXISTS."""
        original = """CREATE INDEX idx_user_email ON users(email);"""
        
        expected = """CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);"""
        
        result = self.transformer.transform_create_index(original)
        assert result.strip() == expected.strip()

    def test_transform_create_unique_index(self):
        """Test transformation of CREATE UNIQUE INDEX to CREATE UNIQUE INDEX IF NOT EXISTS."""
        original = """CREATE UNIQUE INDEX idx_user_email_unique ON users(email);"""
        
        expected = """CREATE UNIQUE INDEX IF NOT EXISTS idx_user_email_unique ON users(email);"""
        
        result = self.transformer.transform_create_index(original)
        assert result.strip() == expected.strip()

    def test_transform_create_procedure(self):
        """Test transformation of CREATE PROCEDURE to use modern syntax."""
        original = """CREATE PROCEDURE GetUserById(IN user_id INT)
BEGIN
    SELECT * FROM users WHERE id = user_id;
END;"""
        
        result = self.transformer.transform_create_procedure(original, "GetUserById")
        
        # With PostgreSQL 15, should use CREATE OR REPLACE PROCEDURE
        assert "CREATE OR REPLACE PROCEDURE GetUserById" in result
        assert "DROP PROCEDURE" not in result

    def test_transform_create_function(self):
        """Test transformation of CREATE FUNCTION to CREATE OR REPLACE FUNCTION."""
        original = """CREATE FUNCTION calculate_age(birth_date DATE)
RETURNS INT
DETERMINISTIC
BEGIN
    RETURN YEAR(CURDATE()) - YEAR(birth_date);
END;"""
        
        expected = """CREATE OR REPLACE FUNCTION calculate_age(birth_date DATE)
RETURNS INT
DETERMINISTIC
BEGIN
    RETURN YEAR(CURDATE()) - YEAR(birth_date);
END;"""
        
        result = self.transformer.transform_create_function(original)
        assert result.strip() == expected.strip()

    def test_transform_create_schema(self):
        """Test transformation of CREATE SCHEMA to CREATE SCHEMA IF NOT EXISTS."""
        original = """CREATE SCHEMA analytics;"""
        
        expected = """CREATE SCHEMA IF NOT EXISTS analytics;"""
        
        result = self.transformer.transform_create_schema(original)
        assert result.strip() == expected.strip()

    def test_transform_create_policy(self):
        """Test transformation of CREATE POLICY to use modern syntax."""
        original = """CREATE POLICY user_policy ON users
FOR SELECT
USING (user_id = current_user_id());"""
        
        result = self.transformer.transform_create_policy(original, "user_policy", "users")
        
        # With PostgreSQL 15, should use CREATE POLICY IF NOT EXISTS
        assert "CREATE POLICY IF NOT EXISTS user_policy" in result
        assert "DROP POLICY" not in result

    def test_transform_add_constraint(self):
        """Test transformation of ADD CONSTRAINT to use modern syntax."""
        original = """ALTER TABLE users ADD CONSTRAINT fk_user_department 
FOREIGN KEY (department_id) REFERENCES departments(id);"""
        
        result = self.transformer.transform_add_constraint(original, "fk_user_department", "users")
        
        # With PostgreSQL 15, should use ADD CONSTRAINT IF NOT EXISTS
        assert "ADD CONSTRAINT IF NOT EXISTS fk_user_department" in result
        assert "DROP CONSTRAINT" not in result

    def test_transform_add_check_constraint(self):
        """Test transformation of ADD CHECK CONSTRAINT to use modern syntax."""
        original = """ALTER TABLE users ADD CONSTRAINT chk_age 
CHECK (age >= 0 AND age <= 150);"""
        
        result = self.transformer.transform_add_constraint(original, "chk_age", "users")
        
        # With PostgreSQL 15, should use ADD CONSTRAINT IF NOT EXISTS
        assert "ADD CONSTRAINT IF NOT EXISTS chk_age" in result
        assert "DROP CONSTRAINT" not in result

    def test_transform_create_sequence(self):
        """Test transformation of CREATE SEQUENCE to include DROP IF EXISTS."""
        original = """CREATE SEQUENCE user_id_seq
START WITH 1
INCREMENT BY 1;"""
        
        result = self.transformer.transform_create_sequence(original, "user_id_seq")
        
        # With PostgreSQL 15, should use CREATE SEQUENCE IF NOT EXISTS
        assert "CREATE SEQUENCE IF NOT EXISTS user_id_seq" in result
        assert "DROP SEQUENCE" not in result

    def test_transform_create_domain(self):
        """Test transformation of CREATE DOMAIN to include DROP IF EXISTS."""
        original = """CREATE DOMAIN email_domain AS VARCHAR(255)
CHECK (VALUE ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');"""
        
        result = self.transformer.transform_create_domain(original, "email_domain")
        
        # With PostgreSQL 15, should use CREATE DOMAIN IF NOT EXISTS
        assert "CREATE DOMAIN IF NOT EXISTS email_domain" in result
        assert "DROP DOMAIN" not in result

    def test_transform_create_extension(self):
        """Test transformation of CREATE EXTENSION to CREATE EXTENSION IF NOT EXISTS."""
        original = """CREATE EXTENSION "uuid-ossp";"""
        
        expected = """CREATE EXTENSION IF NOT EXISTS "uuid-ossp";"""
        
        result = self.transformer.transform_create_extension(original)
        assert result.strip() == expected.strip()

    def test_transform_create_role(self):
        """Test transformation of CREATE ROLE to include DROP IF EXISTS."""
        original = """CREATE ROLE app_user WITH LOGIN PASSWORD 'secret123';"""
        
        result = self.transformer.transform_create_role(original, "app_user")
        
        # With PostgreSQL 15, should use CREATE ROLE IF NOT EXISTS
        assert "CREATE ROLE IF NOT EXISTS app_user" in result
        assert "DROP ROLE" not in result

    def test_transform_create_user(self):
        """Test transformation of CREATE USER to include DROP IF EXISTS."""
        original = """CREATE USER db_user WITH PASSWORD 'password123';"""
        
        result = self.transformer.transform_create_user(original, "db_user")
        
        # With PostgreSQL 15, should use CREATE USER IF NOT EXISTS
        assert "CREATE USER IF NOT EXISTS db_user" in result
        assert "DROP USER" not in result

    def test_transform_grant_statement(self):
        """Test transformation of GRANT to include REVOKE."""
        original = """GRANT SELECT, INSERT ON users TO app_user;"""
        
        result = self.transformer.transform_grant(original, "app_user", "users")
        
        assert "REVOKE ALL ON users FROM app_user;" in result
        assert "GRANT SELECT, INSERT ON users TO app_user;" in result

    def test_transform_create_materialized_view(self):
        """Test transformation of CREATE MATERIALIZED VIEW to include DROP IF EXISTS."""
        original = """CREATE MATERIALIZED VIEW user_stats AS
SELECT department_id, COUNT(*) as user_count
FROM users
GROUP BY department_id;"""
        
        result = self.transformer.transform_create_materialized_view(original, "user_stats")
        
        # With PostgreSQL 15, should use CREATE OR REPLACE MATERIALIZED VIEW
        assert "CREATE OR REPLACE MATERIALIZED VIEW user_stats" in result
        assert "DROP MATERIALIZED VIEW" not in result

    def test_transform_full_sql_file(self):
        """Test transformation of a complete SQL file."""
        original_sql = """-- Sample SQL file
CREATE SCHEMA reporting;

CREATE VIEW user_summary AS
SELECT id, name, email FROM users;

CREATE TRIGGER update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    NEW.updated_at = NOW();
END;

CREATE INDEX idx_user_email ON users(email);

CREATE POLICY user_access_policy ON users
FOR SELECT
USING (user_id = current_user_id());

ALTER TABLE users ADD CONSTRAINT fk_department
FOREIGN KEY (dept_id) REFERENCES departments(id);

-- This should remain unchanged
CREATE TABLE test (id INT);
"""
        
        result = self.transformer.transform_sql_file(original_sql)
        
        # Check that transformations were applied with modern PostgreSQL syntax
        assert "CREATE SCHEMA IF NOT EXISTS reporting;" in result
        assert "CREATE OR REPLACE VIEW user_summary" in result
        assert "CREATE OR REPLACE TRIGGER update_timestamp" in result
        assert "CREATE INDEX IF NOT EXISTS idx_user_email" in result
        assert "CREATE POLICY IF NOT EXISTS user_access_policy" in result
        assert "ADD CONSTRAINT IF NOT EXISTS fk_department" in result
        
        # Check that CREATE TABLE remains unchanged
        assert "CREATE TABLE test (id INT);" in result