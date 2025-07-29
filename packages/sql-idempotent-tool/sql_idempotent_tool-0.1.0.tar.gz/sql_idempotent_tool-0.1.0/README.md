# SQL Idempotent Tool

A sophisticated CLI tool that analyzes SQL files and automatically transforms non-idempotent statements into idempotent ones. This tool helps ensure that SQL scripts can be run multiple times safely without causing errors or unintended side effects.

## Features

### 🔍 **Comprehensive SQL Statement Support**
- **Views**: `CREATE VIEW` → `CREATE OR REPLACE VIEW`
- **Materialized Views**: `CREATE MATERIALIZED VIEW` → `DROP IF EXISTS` + `CREATE`
- **Triggers**: `CREATE TRIGGER` → `DROP IF EXISTS` + `CREATE`
- **Types**: `CREATE TYPE` → `DROP IF EXISTS` + `CREATE`
- **Indexes**: `CREATE INDEX` → `CREATE INDEX IF NOT EXISTS`
- **Functions**: `CREATE FUNCTION` → `CREATE OR REPLACE FUNCTION`
- **Procedures**: `CREATE PROCEDURE` → `DROP IF EXISTS` + `CREATE`
- **Schemas**: `CREATE SCHEMA` → `CREATE SCHEMA IF NOT EXISTS`
- **Policies**: `CREATE POLICY` → `DROP IF EXISTS` + `CREATE`
- **Sequences**: `CREATE SEQUENCE` → `DROP IF EXISTS` + `CREATE`
- **Domains**: `CREATE DOMAIN` → `DROP IF EXISTS` + `CREATE`
- **Extensions**: `CREATE EXTENSION` → `CREATE EXTENSION IF NOT EXISTS`
- **Roles**: `CREATE ROLE` → `DROP IF EXISTS` + `CREATE`
- **Users**: `CREATE USER` → `DROP IF EXISTS` + `CREATE`
- **Grants**: `GRANT` → `REVOKE ALL` + `GRANT`
- **Constraints**: `ALTER TABLE ADD CONSTRAINT` → `DROP IF EXISTS` + `ADD`

### ⚙️ **Advanced Configuration System**
- **TOML-based configuration** with sensible defaults
- **Per-statement-type configuration** (enable/disable, strategy selection)
- **Custom transformation templates**
- **Parser settings** (case sensitivity, comment handling)
- **Output formatting options**

### 🛠️ **Powerful CLI Interface**
- **Analysis mode**: Identify non-idempotent statements
- **Transformation mode**: Convert statements to idempotent form
- **Validation mode**: Check if files are already idempotent
- **Batch processing**: Handle multiple files and directories
- **Configuration management**: Initialize, view, and modify settings

### 🎯 **Smart Parsing**
- **Tree-sitter integration** for accurate SQL parsing
- **Regex fallback** for compatibility
- **Multi-line statement support**
- **Comment preservation**
- **Complex SQL construct handling** (CTEs, subqueries, etc.)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd sql-idempotent-tool

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

## Quick Start

### 1. Analyze a SQL file
```bash
sql-idempotent analyze sample.sql
```

### 2. Transform a SQL file
```bash
sql-idempotent transform sample.sql --output sample_idempotent.sql
```

### 3. Validate a SQL file
```bash
sql-idempotent validate sample.sql
```

## CLI Commands

### `analyze`
Analyze a SQL file and identify non-idempotent statements.

```bash
sql-idempotent analyze [OPTIONS] FILE_PATH

Options:
  --config, -c PATH    Path to config file
  --verbose, -v        Show detailed output
  --help              Show this message and exit
```

**Example:**
```bash
sql-idempotent analyze complex_sample.sql --verbose
```

### `transform`
Transform SQL statements to make them idempotent.

```bash
sql-idempotent transform [OPTIONS] FILE_PATH

Options:
  --output, -o PATH           Output file path
  --config, -c PATH           Path to config file
  --dry-run                   Show preview without making changes
  --verbose, -v               Show detailed output
  --safe-mode/--no-safe-mode  Use conditional blocks instead of DROP+CREATE (default: enabled)
  --format/--no-format        Format output SQL using SQLFluff (default: enabled)
  --help                      Show this message and exit
```

**Examples:**
```bash
# Transform and save to new file
sql-idempotent transform sample.sql --output sample_idempotent.sql

# Preview changes without saving
sql-idempotent transform sample.sql --dry-run

# Transform in place (overwrites original)
sql-idempotent transform sample.sql

# Use safe mode to preserve dependencies (default)
sql-idempotent transform sample.sql --safe-mode

# Use regular mode for more concise output
sql-idempotent transform sample.sql --no-safe-mode

# Format output with SQLFluff (default)
sql-idempotent transform sample.sql --format

# Skip formatting for faster processing
sql-idempotent transform sample.sql --no-format
```

#### Safe Mode vs Regular Mode

The tool offers two transformation strategies:

**Safe Mode (--safe-mode, default):**
- Uses PostgreSQL DO blocks with conditional existence checks
- **Preserves database dependencies** - never drops existing objects
- Safer for production environments where objects may have dependencies
- Example output:
```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'my_view') THEN
        EXECUTE 'CREATE VIEW my_view AS SELECT * FROM users';
    END IF;
END $$;
```

**Regular Mode (--no-safe-mode):**
- Uses modern PostgreSQL syntax like `CREATE OR REPLACE` and `IF NOT EXISTS`
- More concise and readable output
- Faster execution but may break dependencies if objects are referenced elsewhere
- Example output:
```sql
CREATE OR REPLACE VIEW my_view AS SELECT * FROM users;
```

**When to use Safe Mode:**
- Production databases with complex dependencies
- When you're unsure about object relationships
- When preserving existing objects is critical
- In CI/CD pipelines where safety is paramount

**When to use Regular Mode:**
- Development environments
- When you want cleaner, more readable SQL
- When you're certain about dependencies
- For better performance in simple scenarios

#### SQL Formatting

The tool includes automatic SQL formatting using [SQLFluff](https://sqlfluff.com/), a popular SQL linter and formatter.

**Features:**
- **Automatic formatting** - Formats transformed SQL for better readability
- **Configurable dialect** - Supports PostgreSQL, MySQL, SQLite, and more
- **Custom rules** - Use your own SQLFluff configuration file
- **Optional** - Can be disabled for faster processing

**Configuration:**
```toml
[output]
format_sql = true                    # Enable/disable formatting
sqlfluff_dialect = "postgres"       # SQL dialect
sqlfluff_config_path = ".sqlfluff"  # Path to SQLFluff config (optional)
```

**Benefits:**
- Consistent code style across your SQL files
- Better readability of transformed statements
- Follows SQL best practices and conventions
- Integrates seamlessly with existing SQLFluff workflows

### `validate`
Validate that a SQL file contains only idempotent statements.

```bash
sql-idempotent validate [OPTIONS] FILE_PATH

Options:
  --config, -c PATH    Path to config file
  --strict            Fail on any non-idempotent statements
  --help              Show this message and exit
```

**Examples:**
```bash
# Check if file is idempotent
sql-idempotent validate sample.sql

# Strict validation (exit code 1 if non-idempotent)
sql-idempotent validate sample.sql --strict
```

### `batch`
Process multiple SQL files in a directory.

```bash
sql-idempotent batch [OPTIONS] DIRECTORY

Options:
  --pattern TEXT       File pattern to match (default: *.sql)
  --output-dir PATH    Output directory for transformed files
  --config, -c PATH    Path to config file
  --recursive, -r      Process subdirectories recursively
  --dry-run           Show preview without making changes
  --help              Show this message and exit
```

**Examples:**
```bash
# Process all SQL files in a directory
sql-idempotent batch ./sql-scripts --output-dir ./sql-scripts-idempotent

# Process recursively with custom pattern
sql-idempotent batch ./database --pattern "migration_*.sql" --recursive
```

## Configuration Management

### `config-init`
Initialize a new configuration file.

```bash
sql-idempotent config-init [OPTIONS]

Options:
  --config, -c PATH    Path to create config file
  --force, -f         Overwrite existing config file
  --help              Show this message and exit
```

### `config-show`
Display current configuration settings.

```bash
sql-idempotent config-show [OPTIONS]

Options:
  --config, -c PATH    Path to config file
  --help              Show this message and exit
```

### `config-set`
Set a configuration value.

```bash
sql-idempotent config-set [OPTIONS] KEY VALUE

Options:
  --config, -c PATH    Path to config file
  --help              Show this message and exit
```

**Examples:**
```bash
# Disable transformation for triggers
sql-idempotent config-set transformations.CREATE_TRIGGER.enabled false

# Change strategy for views
sql-idempotent config-set transformations.CREATE_VIEW.strategy drop_and_create

# Enable comment addition
sql-idempotent config-set output.add_comments true
```

## Configuration File

The tool uses TOML configuration files. Here's an example:

```toml
# sql-idempotent.toml

[transformations.CREATE_VIEW]
enabled = true
strategy = "or_replace"

[transformations.CREATE_TRIGGER]
enabled = true
strategy = "drop_and_create"

[transformations.CREATE_INDEX]
enabled = true
strategy = "if_not_exists"

[parser]
case_sensitive = false
ignore_comments = true
excluded_statement_types = []

[output]
preserve_formatting = true
add_comments = true
comment_template = "-- Idempotent transformation applied by sql-idempotent-tool"

# Safety settings
require_confirmation = false
max_file_size_mb = 100
create_backups = true
backup_suffix = ".backup"
```

### Configuration Locations

The tool looks for configuration files in this order:
1. `--config` parameter
2. `./sql-idempotent.toml`
3. `./.sql-idempotent.toml`
4. `~/.config/sql-idempotent/config.toml`
5. `~/.sql-idempotent.toml`

## Transformation Strategies

### `or_replace`
Uses `CREATE OR REPLACE` syntax where supported:
- `CREATE VIEW` → `CREATE OR REPLACE VIEW`
- `CREATE FUNCTION` → `CREATE OR REPLACE FUNCTION`

### `if_not_exists`
Uses `IF NOT EXISTS` syntax where supported:
- `CREATE SCHEMA` → `CREATE SCHEMA IF NOT EXISTS`
- `CREATE INDEX` → `CREATE INDEX IF NOT EXISTS`
- `CREATE EXTENSION` → `CREATE EXTENSION IF NOT EXISTS`

### `drop_and_create`
Adds `DROP IF EXISTS` before the `CREATE` statement:
- `CREATE TRIGGER` → `DROP TRIGGER IF EXISTS` + `CREATE TRIGGER`
- `CREATE TYPE` → `DROP TYPE IF EXISTS` + `CREATE TYPE`

## Examples

### Basic Usage

```sql
-- Input: sample.sql
CREATE VIEW user_summary AS
SELECT id, name, email FROM users;

CREATE TRIGGER update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_modified_time();
```

```bash
sql-idempotent transform sample.sql --output sample_idempotent.sql
```

```sql
-- Output: sample_idempotent.sql
CREATE OR REPLACE VIEW user_summary AS
SELECT id, name, email FROM users;

DROP TRIGGER IF EXISTS update_timestamp;
CREATE TRIGGER update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_modified_time();
```

### Complex Transformations

The tool handles complex SQL constructs including:
- Multi-line statements with comments
- CTEs (Common Table Expressions)
- Complex constraint definitions
- Role-based security policies
- Grant statements with multiple objects

### Batch Processing

```bash
# Process all migration files
sql-idempotent batch ./migrations --pattern "*.sql" --output-dir ./migrations-idempotent

# Validate all files in a directory
find ./sql-scripts -name "*.sql" -exec sql-idempotent validate {} \;
```

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_sql_parser.py

# Run with coverage
uv run pytest --cov=sql_idempotent_tool
```

### Project Structure

```
sql-idempotent-tool/
├── sql_idempotent_tool/
│   ├── __init__.py
│   ├── cli.py              # CLI interface
│   ├── sql_parser.py       # Core parsing and transformation logic
│   └── config.py           # Configuration management
├── tests/
│   └── test_sql_parser.py  # Comprehensive test suite
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Changelog

### v1.0.0
- Initial release with comprehensive SQL statement support
- Configuration system with TOML files
- Advanced CLI with multiple commands
- Tree-sitter integration with regex fallback
- Batch processing capabilities
- Comprehensive test suite

## Support

For issues, feature requests, or questions:
- Open an issue on GitHub
- Check the documentation
- Review the test files for usage examples

---

**Made with ❤️ for the SQL community**