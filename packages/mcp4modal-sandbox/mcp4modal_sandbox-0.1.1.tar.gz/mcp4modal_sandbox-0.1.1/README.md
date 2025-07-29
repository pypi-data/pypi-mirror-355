# MCP4Modal Sandbox

A powerful Model Context Protocol (MCP) server that provides seamless cloud-based sandbox management using Modal.com. This project enables LLMs and AI assistants to spawn, manage, and interact with isolated compute environments in the cloud with full GPU support.

## =� Features

### Core Sandbox Management
- **Launch Sandboxes**: Create isolated Python environments with custom configurations
- **Terminate Sandboxes**: Clean resource management and controlled shutdown
- **List Sandboxes**: Monitor and track active sandbox environments
- **App Namespacing**: Organize sandboxes within Modal app namespaces

### Advanced Configuration
- **Python Versions**: Support for multiple Python versions (default: 3.12)
- **Package Management**: Install pip and apt packages during sandbox creation
- **Resource Allocation**: Configure CPU cores, memory, and execution timeouts
- **Working Directory**: Set custom working directories for sandbox environments

### GPU Support
Comprehensive GPU support for machine learning and compute-intensive workloads:
- **T4**: Entry-level GPU, ideal for inference workloads
- **L4**: Mid-range GPU for general ML tasks
- **A10G**: High-performance GPU for training (up to 4 GPUs)
- **A100-40GB/80GB**: High-end GPUs for large-scale training
- **L40S**: Latest generation GPU for ML workloads
- **H100**: Latest generation high-end GPU
- **H200**: Latest generation flagship GPU
- **B200**: Latest generation enterprise GPU

### File Operations
- **Push Files**: Upload files from local filesystem to sandboxes
- **Pull Files**: Download files from sandboxes to local filesystem
- **Read File Content**: View file contents directly without downloading
- **Write File Content**: Create and edit files within sandboxes
- **Directory Management**: Create, list, and remove directories

### Command Execution
- **Remote Execution**: Run arbitrary commands in sandbox environments
- **Output Capture**: Capture stdout, stderr, and return codes
- **Timeout Control**: Configure execution timeouts for long-running tasks
- **Performance Metrics**: Track execution time and resource usage

### Security & Environment Management
- **Secrets Management**: Inject environment variables and secrets
- **Predefined Secrets**: Reference existing secrets from Modal dashboard
- **Volume Mounting**: Attach persistent storage volumes
- **Isolated Environments**: Complete isolation between sandbox instances

### Transport Options
- **stdio**: Direct command-line interface (default)
- **streamable-http**: HTTP-based communication
- **SSE**: Server-Sent Events for real-time updates

## =� Prerequisites

- Python 3.12+
- Modal.com account and API key
- Environment variables configured (see Configuration section)

## =� Installation

### Using UV (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd mcp4modal_sandbox

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Using Pip
```bash
# Clone the repository
git clone <repository-url>
cd mcp4modal_sandbox

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Using Docker

#### Build the Docker Image
```bash
# Build the Docker image
docker build -t mcp4modal-sandbox .
```

#### Run with stdio Transport (Default)
```bash
# Run with stdio transport (no port mapping needed)
docker run -it \
  -e MODAL_TOKEN_ID="your_modal_token_id" \
  -e MODAL_TOKEN_SECRET="your_modal_token_secret" \
  mcp4modal-sandbox --transport streamable-http
```

#### Run with HTTP Transport
```bash
# Run with streamable-http transport
docker run -p 8000:8000 \
  -e MODAL_TOKEN_ID="your_modal_token_id" \
  -e MODAL_TOKEN_SECRET="your_modal_token_secret" \
  -e MCP_HOST="0.0.0.0" \
  -e MCP_PORT="8000" \
  mcp4modal-sandbox launch-mcp --transport streamable-http

# Run with SSE transport
docker run -p 8000:8000 \
  -e MODAL_TOKEN_ID="your_modal_token_id" \
  -e MODAL_TOKEN_SECRET="your_modal_token_secret" \
  -e MCP_HOST="0.0.0.0" \
  -e MCP_PORT="8000" \
  mcp4modal-sandbox launch-mcp --transport sse

# Run with custom port
docker run -p 3000:3000 \
  -e MODAL_TOKEN_ID="your_modal_token_id" \
  -e MODAL_TOKEN_SECRET="your_modal_token_secret" \
  -e MCP_HOST="0.0.0.0" \
  -e MCP_PORT="3000" \
  mcp4modal-sandbox launch-mcp --transport streamable-http

# Run with environment file
docker run -p 8000:8000 --env-file .env \
  mcp4modal-sandbox launch-mcp --transport streamable-http

# Run in background (detached mode)
docker run -d -p 8000:8000 \
  -e MODAL_TOKEN_ID="your_modal_token_id" \
  -e MODAL_TOKEN_SECRET="your_modal_token_secret" \
  -e MCP_HOST="0.0.0.0" \
  -e MCP_PORT="8000" \
  --name mcp4modal-container \
  mcp4modal-sandbox launch-mcp --transport streamable-http
```

#### Using Docker Compose
```bash
# Create .env file with your Modal credentials
cat > .env << EOF
MODAL_TOKEN_ID=your_modal_token_id
MODAL_TOKEN_SECRET=your_modal_token_secret
MCP_HOST=0.0.0.0
MCP_PORT=8000
EOF

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

## � Configuration

### Environment Variables
Create a `.env` file in the project root:

```bash
# Required: Modal.com API Configuration
MODAL_TOKEN_ID="your_modal_token_id"
MODAL_TOKEN_SECRET="your_modal_token_secret"

# Optional: HTTP Transport Configuration (only needed for streamable-http/sse transports)
MCP_HOST="0.0.0.0"  # Default: 0.0.0.0
MCP_PORT=8000       # Default: 8000
```

### Modal.com Setup
1. Create an account at [Modal.com](https://modal.com)
2. Generate API tokens from your Modal dashboard
3. Configure the tokens in your environment variables

## =� Usage

### Starting the MCP Server

#### stdio Transport (Default)
```bash
# Using the installed command
mcp4modal-sandbox launch-mcp

# Using Python module
python -m mcp4modal_sandbox launch-mcp

# Using uv
uv run python -m mcp4modal_sandbox launch-mcp
```

#### HTTP Transport
```bash
# Start HTTP server
mcp4modal-sandbox launch-mcp --transport streamable-http

# Start SSE server
mcp4modal-sandbox launch-mcp --transport sse
```

### Integration with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "mcp4modal-sandbox": {
      "command": "mcp4modal-sandbox",
      "args": ["launch-mcp"],
      "env": {
        "MODAL_TOKEN_ID": "your_modal_token_id",
        "MODAL_TOKEN_SECRET": "your_modal_token_secret"
      }
    }
  }
}
```

## =' Available Tools

### Sandbox Lifecycle Management

#### `launch_sandbox`
Create a new sandbox with custom configuration.

**Parameters:**
- `app_name` (required): Modal app namespace for sandbox grouping
- `python_version`: Python version (default: "3.12")
- `pip_packages`: List of pip packages to install
- `apt_packages`: List of apt packages to install
- `timeout_seconds`: Maximum runtime (default: 600)
- `cpu`: CPU cores (default: 2.0)
- `memory`: Memory in MB (default: 4096)
- `secrets`: Dictionary of environment variables
- `inject_predefined_secrets`: List of predefined secret names
- `volumes`: Dictionary of volume mounts
- `workdir`: Working directory (default: "/")
- `gpu_type`: GPU type (optional)
- `gpu_count`: Number of GPUs (optional)

**Example:**
```python
# Launch a GPU-enabled sandbox for machine learning
response = await launch_sandbox(
    app_name="ml-experiments",
    python_version="3.11",
    pip_packages=["torch", "transformers", "numpy"],
    gpu_type="A100-40GB",
    gpu_count=1,
    memory=16384,
    cpu=4.0
)
```

#### `terminate_sandbox`
Stop and clean up a running sandbox.

**Parameters:**
- `sandbox_id` (required): Unique sandbox identifier

#### `list_sandboxes`
List all sandboxes within an app namespace.

**Parameters:**
- `app_name` (required): Modal app namespace

### Command Execution

#### `execute_command`
Run commands in a sandbox environment.

**Parameters:**
- `sandbox_id` (required): Target sandbox identifier
- `command` (required): List of command arguments
- `timeout_seconds`: Command timeout (default: 30)

**Example:**
```python
# Run a Python script with arguments
response = await execute_command(
    sandbox_id="sb-123456",
    command=["python", "train.py", "--epochs", "10"],
    timeout_seconds=3600
)
```

### File Operations

#### `push_file_to_sandbox`
Upload files from local filesystem to sandbox.

**Parameters:**
- `sandbox_id` (required): Target sandbox
- `local_path` (required): Source file path
- `sandbox_path` (required): Destination path in sandbox
- `read_file_mode`: File read mode (default: "rb")
- `writefile_mode`: File write mode (default: "wb")

#### `pull_file_from_sandbox`
Download files from sandbox to local filesystem.

**Parameters:**
- `sandbox_id` (required): Source sandbox
- `sandbox_path` (required): Source file path in sandbox
- `local_path` (required): Destination path locally

#### `read_file_content_from_sandbox`
Read file contents without downloading.

**Parameters:**
- `sandbox_id` (required): Target sandbox
- `path` (required): File path in sandbox

#### `write_file_content_to_sandbox`
Create or edit files within sandbox.

**Parameters:**
- `sandbox_id` (required): Target sandbox
- `sandbox_path` (required): File path in sandbox
- `content` (required): Content to write

### Directory Management

#### `list_directory`
List directory contents in sandbox.

**Parameters:**
- `sandbox_id` (required): Target sandbox
- `path` (required): Directory path

#### `make_directory`
Create directories in sandbox.

**Parameters:**
- `sandbox_id` (required): Target sandbox
- `path` (required): Directory path to create
- `parents`: Create parent directories (default: false)

#### `remove_path`
Remove files or directories from sandbox.

**Parameters:**
- `sandbox_id` (required): Target sandbox
- `path` (required): Path to remove
- `recursive`: Remove recursively (default: false)

## =� Use Cases

### Machine Learning Development
```python
# Launch ML sandbox with GPU
sandbox = await launch_sandbox(
    app_name="ml-research",
    pip_packages=["torch", "transformers", "datasets", "wandb"],
    gpu_type="A100-40GB",
    memory=32768,
    secrets={"WANDB_API_KEY": "your_key"}
)

# Upload training data
await push_file_to_sandbox(
    sandbox_id=sandbox.sandbox_id,
    local_path="./training_data.json",
    sandbox_path="/data/training_data.json"
)

# Run training
await execute_command(
    sandbox_id=sandbox.sandbox_id,
    command=["python", "train.py", "--data", "/data/training_data.json"],
    timeout_seconds=7200
)
```

### Data Processing Pipeline
```python
# Launch processing environment
sandbox = await launch_sandbox(
    app_name="data-pipeline",
    pip_packages=["pandas", "numpy", "scikit-learn"],
    apt_packages=["wget", "unzip"],
    cpu=8.0,
    memory=16384
)

# Process data
await execute_command(
    sandbox_id=sandbox.sandbox_id,
    command=["python", "process_data.py", "--input", "/data/raw", "--output", "/data/processed"]
)

# Download results
await pull_file_from_sandbox(
    sandbox_id=sandbox.sandbox_id,
    sandbox_path="/data/processed/results.csv",
    local_path="./results.csv"
)
```

### Code Testing and Validation
```python
# Launch testing environment
sandbox = await launch_sandbox(
    app_name="testing",
    pip_packages=["pytest", "coverage", "mypy"],
    python_version="3.11"
)

# Upload code
await push_file_to_sandbox(
    sandbox_id=sandbox.sandbox_id,
    local_path="./src/",
    sandbox_path="/code/"
)

# Run tests
test_result = await execute_command(
    sandbox_id=sandbox.sandbox_id,
    command=["python", "-m", "pytest", "/code/tests/", "-v"]
)
```

## <� Architecture

### Core Components

#### MCPServer (`src/mcp4modal_sandbox/backend/mcp_server.py`)
- Main server class managing MCP protocol communication
- Handles tool registration and request routing
- Manages sandbox lifecycle and operations
- Integrates with Modal.com APIs

#### Settings Management (`src/mcp4modal_sandbox/settings.py`)
- Pydantic-based configuration management
- Environment variable validation and parsing
- Server configuration options

#### Response Schemas (`src/mcp4modal_sandbox/backend/response_schema.py`)
- Structured response models using Pydantic
- Type safety and validation for all API responses
- Consistent data formats across operations

#### Tool Descriptions (`src/mcp4modal_sandbox/backend/tool_descriptions.py`)
- Comprehensive documentation for all available tools
- Parameter specifications and usage examples
- Integration guidelines for LLM consumption

### Dependencies

#### Core Dependencies
- **FastMCP**: MCP protocol implementation
- **Modal**: Cloud compute platform integration
- **Pydantic**: Data validation and settings management
- **Click**: Command-line interface framework
- **PyZMQ**: Asynchronous messaging
- **Uvicorn**: ASGI server for HTTP transport

#### Development Dependencies
- **pytest**: Testing framework
- **mypy**: Static type checking
- **black**: Code formatting
- **ruff**: Fast Python linter

## >� Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/mcp4modal_sandbox

# Run specific test file
pytest tests/test_mcp_server.py
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Local Development
```bash
# Install in development mode
uv pip install -e .

# Run server locally
python -m mcp4modal_sandbox launch-mcp --transport streamable-http
```

## = Security Considerations

### API Key Management
- Store Modal.com API keys securely
- Use environment variables, never hardcode secrets
- Rotate API keys regularly
- Use Modal's predefined secrets for sensitive data

### Sandbox Isolation
- Sandboxes are completely isolated from each other
- No network access between sandboxes by default
- Resource limits prevent resource exhaustion
- Automatic cleanup prevents resource leaks

### Network Security
- Configure firewall rules for HTTP transport
- Use HTTPS in production environments
- Implement authentication for public deployments
- Monitor sandbox resource usage

## =� Monitoring and Logging

### Built-in Logging
- Structured logging with timestamps and levels
- Operation tracking and performance metrics
- Error reporting and debugging information
- Configurable log levels

### Monitoring Integration
- Compatible with standard logging frameworks
- Metrics exposure for monitoring systems
- Health check endpoints for HTTP transport
- Resource usage tracking

## > Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages

## =� License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## =O Acknowledgments

- [Modal.com](https://modal.com) for providing the cloud compute platform
- [Anthropic](https://anthropic.com) for the Model Context Protocol specification
- [FastMCP](https://github.com/jlowin/fastmcp) for the MCP implementation framework

## <� Support

### Common Issues

#### Modal Authentication Errors
- Verify your Modal.com API keys are correct
- Ensure your Modal account has sufficient credits
- Check network connectivity to Modal's API

#### Sandbox Launch Failures
- Verify resource limits (CPU, memory, GPU availability)
- Check package compatibility and versions
- Review Modal's service status

#### Connection Issues
- Verify network connectivity
- Check firewall settings for HTTP transport
- Ensure correct transport configuration

### Getting Help
- Open an issue on GitHub for bug reports
- Check Modal.com documentation for API limits
- Review logs for detailed error information

## =. Future Roadmap

### Planned Features
- **Persistent Storage**: Enhanced volume management and data persistence
- **Network Policies**: Advanced networking and security configurations
- **Batch Operations**: Bulk sandbox management operations
- **Monitoring Dashboard**: Web-based monitoring and management interface
- **Auto-scaling**: Dynamic resource allocation based on workload
- **Integration Templates**: Pre-configured setups for common use cases

### Performance Improvements
- Connection pooling and caching
- Optimized file transfer protocols
- Enhanced error handling and retry mechanisms
- Resource usage optimization

---

For more information, visit our [GitHub repository](https://github.com/milkymap/mcp4modal_sandbox) or check out the [Modal.com documentation](https://modal.com/docs).