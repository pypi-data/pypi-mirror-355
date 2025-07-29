-- Sample SQL file with non-idempotent statements
CREATE SCHEMA reporting;

CREATE VIEW user_summary AS
SELECT id, name, email, created_at FROM users
WHERE status = 'active';

CREATE TRIGGER update_user_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
BEGIN
    NEW.updated_at = NOW();
END;

CREATE UNIQUE INDEX idx_user_email_unique ON users(email);

CREATE TYPE user_status AS ENUM ('active', 'inactive', 'pending');

CREATE FUNCTION get_user_count()
RETURNS INT
DETERMINISTIC
BEGIN
    RETURN (SELECT COUNT(*) FROM users);
END;

CREATE POLICY user_access_policy ON users
FOR SELECT
USING (user_id = current_user_id());

ALTER TABLE users ADD CONSTRAINT fk_user_department
FOREIGN KEY (department_id) REFERENCES departments(id);

ALTER TABLE users ADD CONSTRAINT chk_user_age
CHECK (age >= 0 AND age <= 150);

-- This should remain unchanged
CREATE TABLE test_table (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

-- This is already idempotent
CREATE OR REPLACE VIEW existing_view AS
SELECT * FROM test_table;