# Dependency Manager (DepMan)

A universal dependency manager for various package managers and programming languages.

## Features

- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Multi-Language Support**: Manages dependencies for various programming languages (Python, JavaScript, Java, Ruby, Go, Rust, etc.)
- **Unified Interface**: Common commands for all package managers
- **Project & Global Management**: Handle both project-specific and global dependencies

## Usage

```bash
# Install a package globally
depman install <package_name>

# Install a package for the current project
depman install <package_name> --project

# Install all dependencies for the current project
depman install --project

# Uninstall a package
depman uninstall <package_name>

# Upgrade a package
depman upgrade <package_name>

# Upgrade all packages
depman upgrade --all

# Scan project for dependencies
depman scan

# List all installed dependencies
depman list

# Show dependency tree
depman tree

# Find a package's installation path
depman path <package_name>

# Search for packages
depman search <keyword>
```

## Installation

```bash
# Install from PyPI
pip install depman
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/username/dependency_manager.git
cd dependency_manager

# Install the package
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Supported Package Managers

### Currently Implemented

#### Operating System Package Managers
- ✅ Homebrew (macOS)

#### Language Package Managers
- ✅ pip (Python)
- ✅ npm (JavaScript/Node.js)

### Coming Soon

#### Operating System Package Managers
- APT (Debian/Ubuntu)
- Chocolatey (Windows)

#### Language Package Managers
- yarn, pnpm (JavaScript/Node.js)
- Poetry, pipenv (Python)
- Maven, Gradle (Java)
- Bundler, RubyGems (Ruby)
- Go Modules (Go)
- Cargo (Rust)
- Composer (PHP)
- NuGet (.NET)

## Examples

Example projects for different package managers can be found in the `examples` directory:

- `examples/python_project`: A simple Python project with pip dependencies
- `examples/node_project`: A simple Node.js project with npm dependencies

## License

MIT 