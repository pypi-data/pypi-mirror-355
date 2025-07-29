# lam
Lam is a data transformation tool for Laminar that supports both `jq` and JavaScript transformations using Bun.

## Quickstart
Install the dependencies:
```bash
# For JQ support
brew install jq  # or sudo apt-get install jq

# For JavaScript support
curl -fsSL https://bun.sh/install | bash

make setup
```

Run the CLI tool:
```bash
make cli ARGS="run <program> <input> [--language jq|js]"
```

## Features
- JQ transformations (default)
- JavaScript transformations with Bun runtime
- Built-in utilities (lodash, date-fns)
- Resource monitoring and limits
- Detailed execution statistics
- Secure execution environment

## Examples

### JQ Transform
```bash
make cli ARGS="run examples/transform.jq data.json"
```

### JavaScript Transform
```bash
make cli ARGS="run examples/transform.js data.json --language js"
```

Example JavaScript transform:
```javascript
(input) => {
    // Lodash available as _
    return _.map(input.data, item => ({
        value: item.value * 2
    }));
}
```

## Installation

### Docker Installation
```dockerfile
# Install lam-cli
RUN pip3 install git+https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/user/project.git@{version}

# Install dependencies
RUN apt-get update && apt-get install -y jq
RUN curl -fsSL https://bun.sh/install | bash
```

### Manual Setup
Create a virtual environment and install dependencies:
```bash
python3 -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
# Basic usage
python3 ./lam/lam.py run <program> <input>

# With JavaScript
python3 ./lam/lam.py run script.js data.json --language js

# Full options
python3 ./lam/lam.py run <program> <input> \
    --language [jq|js] \
    --workspace_id <id> \
    --flow_id <id> \
    --execution_id <id> \
    [--as-json]
```

## Resource Limits
- Maximum input size: 10MB
- Execution timeout: 5 seconds
- Memory limits enabled
- Disk space monitoring

## Security
- Sandboxed JavaScript execution
- Network access disabled
- Limited global scope
- Resource monitoring
- Secure dependency management

## Logging and Monitoring
- Execution statistics (duration, memory usage)
- Detailed error tracking
- PostHog analytics integration
- Log file generation

## Development
```bash
# Run all tests
make test

# Run specific test suite
make test-jq
make test-js
make test-js-edge-cases

# Run single test
make test-single TEST=test/js/example.js DATA=test/data/input.json

# Or
python -m lam.lam run --language js test/js/simple.js test/data/simple.json
```

## Releases
Update version in `setup.py`:
```python
setup(
    name="lam-cli",
    version="0.0.<x>",
    ...
)
```

Create and push tag:
```bash
git tag v<version>-<increment>
git push origin v<version>-<increment>
```

## Dependencies
Update dependencies:
```bash
pip3 install <package>
pip3 freeze > requirements.txt
```

## Install Locally

```bash
pip3 install -e .
```

## Troubleshooting

### Package Installation Issues
If you encounter issues installing the package with pip, particularly with the certifi dependency, you may see errors like:

```bash
error: uninstall-no-record-file
× Cannot uninstall certifi None
╰─> The package's contents are unknown: no RECORD file was found for certifi.
```
This can happen when multiple Python versions are installed or when system packages have been modified. Try these steps:

First, identify which Python version you're using:

```bash
which python3
python3 --version
which pip3
```

Remove the problematic certifi installation (adjust path based on your Python version):

```bash
sudo rm -rf /usr/local/lib/python3.13/site-packages/certifi
```

Install certifi directly:

```bash
pip3 install --ignore-installed certifi --break-system-packages
```

Then try installing lam-cli again:

```bash
pip3 install . --break-system-packages
```