# helm-values-manager

[![CI](https://github.com/Zipstack/helm-values-manager/workflows/CI/badge.svg)](https://github.com/Zipstack/helm-values-manager/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-check%20CI-blue)](https://github.com/Zipstack/helm-values-manager/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![Helm Plugin](https://img.shields.io/badge/helm-plugin-blue.svg)](https://helm.sh/docs/topics/plugins/)

A Helm plugin that helps manage Helm value configurations across different deployments (dev, test, prod) with a schema-driven approach. It separates value definitions (schema) from actual values, enabling vendors to distribute schemas while customers manage their deployment-specific values securely.

## Features

- **Schema-driven configuration**: Define value metadata (descriptions, paths, requirements) separately from actual values
- **Multi-environment support**: Manage values for different deployments in a single workflow
- **Secret management**: Support for environment variables with pluggable architecture for future providers
- **CD system agnostic**: Generates standard values.yaml files usable with any CD system
- **Type safety**: JSON-based configuration with validation
- **Interactive CLI**: Commands to add/update/remove both schema entries and values

## Installation

### As a Standalone CLI Tool (Recommended)

Install from GitHub:

```bash
pip install git+https://github.com/Zipstack/helm-values-manager.git
```

Or clone and install locally:

```bash
git clone https://github.com/Zipstack/helm-values-manager
cd helm-values-manager
pip install -e .
```

Or with uv:

```bash
git clone https://github.com/Zipstack/helm-values-manager
cd helm-values-manager
uv sync
# CLI will be available as: uv run helm-values-manager
```

The standalone installation provides better shell completion support and is easier to manage.

### As a Helm Plugin

Install the plugin using the Helm plugin manager:

```bash
helm plugin install https://github.com/Zipstack/helm-values-manager
```

Or install from source:

```bash
git clone https://github.com/Zipstack/helm-values-manager
helm plugin install ./helm-values-manager
```

**Note**: The helm plugin installation has limited shell completion support due to the plugin wrapper architecture.

## Quick Start

### Vendor Workflow (Chart Publisher)

1. **Initialize schema**:
   ```bash
   helm values-manager init
   ```

2. **Add schema definitions**:
   ```bash
   helm values-manager schema add
   # Interactive prompts for: key, path, description, type, required, etc.
   ```

3. **Distribute schema.json** alongside your Helm chart

### Customer Workflow (Chart User)

1. **Set up environment values**:
   ```bash
   # Set regular values
   helm values-manager values set database-host "prod-db.example.com" --env prod

   # Set secrets (uses environment variables)
   helm values-manager values set-secret database-password --env prod
   ```

2. **Generate values.yaml for deployment**:
   ```bash
   export PROD_DB_PASSWORD="actual-secret-password"
   helm values-manager generate --env prod > values-prod.yaml
   ```

3. **Deploy with Helm**:
   ```bash
   helm upgrade myapp ./chart -f values-prod.yaml
   ```

## Command Reference

> **Note**: Use `helm-values-manager` for standalone installation or `helm values-manager` for helm plugin installation.

| Command | Description |
|---------|-------------|
| `helm values-manager init` | Initialize a new schema.json file |
| `helm values-manager validate [--env ENV]` | Validate schema and values |
| `helm values-manager generate --env ENV` | Generate values.yaml for deployment |

### Schema Management

| Command | Description |
|---------|-------------|
| `helm values-manager schema add` | Add new value to schema (interactive) |
| `helm values-manager schema list` | List all schema entries |
| `helm values-manager schema get KEY` | Show details of specific schema entry |
| `helm values-manager schema update KEY` | Update existing schema entry |
| `helm values-manager schema remove KEY` | Remove entry from schema |

### Values Management

| Command | Description |
|---------|-------------|
| `helm values-manager values set KEY VALUE --env ENV` | Set or update a value |
| `helm values-manager values set-secret KEY --env ENV` | Configure secret (interactive) |
| `helm values-manager values get KEY --env ENV` | Get specific value |
| `helm values-manager values list --env ENV` | List all values for environment |
| `helm values-manager values remove KEY --env ENV` | Remove a value |
| `helm values-manager values init --env ENV` | Interactive setup for environment |

### Global Options

All commands support these options:
- `--schema PATH`: Path to schema.json (default: ./schema.json)
- `--values PATH`: Base path for values files (default: ./values-{env}.json)

## Shell Completion

The CLI supports shell completion for enhanced productivity.

### Setup

**For Helm Plugin Installation:**
```bash
# Install completion for your shell (bash, zsh, fish, powershell)
helm values-manager --install-completion zsh

# Restart your shell or source the configuration
source ~/.zshrc  # for zsh
source ~/.bashrc # for bash
```

**For Standalone Installation:**
```bash
# Install completion for your shell
helm-values-manager --install-completion zsh

# Restart your shell or source the configuration
source ~/.zshrc  # for zsh
source ~/.bashrc # for bash
```

### Usage

After setup, you can use tab completion:
```bash
# Tab completion for commands
helm values-manager <TAB><TAB>

# Tab completion for subcommands
helm values-manager schema <TAB><TAB>
helm values-manager values <TAB><TAB>

# Show available completion script (without installing)
helm values-manager --show-completion zsh
```

### Supported Shells

- **bash**: Most common Linux/macOS shell
- **zsh**: Default macOS shell (macOS 10.15+)
- **fish**: Modern shell with advanced features
- **PowerShell**: Windows PowerShell and PowerShell Core

## File Structure

```
project/
├── schema.json              # Value definitions (from vendor)
├── values-dev.json         # Customer's values for dev environment
├── values-staging.json     # Customer's values for staging
└── values-prod.json        # Customer's values for production
```

### Schema File Example

```json
{
  "version": "1.0",
  "values": [
    {
      "key": "database-host",
      "path": "database.host",
      "description": "PostgreSQL database hostname",
      "type": "string",
      "required": true,
      "default": "localhost"
    },
    {
      "key": "database-password",
      "path": "database.password",
      "description": "PostgreSQL password",
      "type": "string",
      "required": true,
      "sensitive": true
    },
    {
      "key": "replicas",
      "path": "deployment.replicas",
      "type": "number",
      "required": false,
      "default": 3
    }
  ]
}
```

### Values File Example

```json
{
  "database-host": "prod-db.example.com",
  "database-password": {
    "type": "env",
    "name": "PROD_DB_PASSWORD"
  },
  "replicas": 5
}
```

## Security Best Practices

### Secret Management

1. **Never store actual secrets in values files** - Use environment variable references:
   ```json
   {
     "database-password": {
       "type": "env",
       "name": "PROD_DB_PASSWORD"
     }
   }
   ```

2. **Set environment variables before generation**:
   ```bash
   export PROD_DB_PASSWORD="actual-secret"
   helm values-manager generate --env prod
   ```

3. **Pipe output directly to Helm** to avoid writing secrets to disk:
   ```bash
   helm values-manager generate --env prod | helm upgrade myapp ./chart -f -
   ```

### File Permissions

- Ensure generated values.yaml has appropriate permissions (600)
- Consider using CI/CD environment variables instead of local files
- Never commit generated values.yaml files to version control

## Troubleshooting

### Common Errors

**Error: Missing required value: database-host (env: prod)**
- Solution: Set the missing value with `helm values-manager values set database-host "value" --env prod`

**Error: Environment variable not found: PROD_DB_PASSWORD**
- Solution: Export the environment variable before generation: `export PROD_DB_PASSWORD="secret"`

**Error: Type mismatch: replicas should be number, got string**
- Solution: Ensure numeric values are not quoted: `helm values-manager values set replicas 3 --env prod`

**Error: Schema file not found: schema.json**
- Solution: Run `helm values-manager init` to create a schema file, or use `--schema` flag to specify path

**Error: Key 'unknown-key' not found in schema**
- Solution: Add the key to schema first with `helm values-manager schema add`, or check for typos

### Validation Issues

Run validation to see all issues at once:
```bash
helm values-manager validate --env prod
```

This will show all missing values, type mismatches, and other validation errors.

### Debug Mode

For detailed error information, use the validation command:
```bash
helm values-manager validate  # Validates all environments
helm values-manager validate --env prod  # Validates specific environment
```

## Development

This plugin is written in Python and uses:
- **CLI Framework**: Typer
- **Dependencies**: PyYAML for YAML generation
- **Testing**: pytest with comprehensive test coverage
- **Testing Tool**: tox for consistent testing across environments

### Building from Source

```bash
git clone https://github.com/Zipstack/helm-values-manager
cd helm-values-manager
uv sync  # Install dependencies
```

### Setting up Pre-commit Hooks

We use pre-commit hooks to ensure code quality. To set them up:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run hooks manually (optional)
uv run pre-commit run --all-files
```

The pre-commit hooks will automatically run:
- Code formatting with Ruff
- Linting checks
- Type checking with mypy
- Unit tests with pytest
- JSON/YAML validation
- Trailing whitespace removal

### Running Tests

We use tox for consistent testing across different Python versions and environments:

```bash
# Run tests for current Python version
tox

# Run tests for specific Python version
tox -e py311

# Run linting
tox -e lint

# Run type checking
tox -e type-check

# Run integration tests
tox -e integration

# Run all environments
tox -p  # parallel execution
```

You can also use tox via uv (if you have uv installed):

```bash
# Same commands work with uv
uv run tox -e lint
uv run tox -e py311
```

### Alternative: Direct pytest (for development)

```bash
# Using uv
uv run pytest

# Using pip
pip install -e .[dev]
pytest
```

### Why Tox?

Tox ensures consistent test environments between local development and CI:
- Isolated virtual environments for each test run
- Consistent dependency installation across different Python versions
- Environment variable standardization (NO_COLOR, FORCE_COLOR)
- Cross-platform compatibility
- Works reliably both with direct `tox` commands and via `uv run tox`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[MIT License](LICENSE)
