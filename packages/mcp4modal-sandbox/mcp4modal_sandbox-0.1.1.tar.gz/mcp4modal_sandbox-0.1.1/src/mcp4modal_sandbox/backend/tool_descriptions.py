from enum import Enum

class ToolDescriptions(str, Enum):
    LAUNCH_SANDBOX = """
            Launches a new Modal sandbox with specified configuration.
            
            Parameters:
            - python_version: Python version to use (default: "3.12")
            - pip_packages: List of pip packages to install
            - apt_packages: List of apt packages to install
            - timeout_seconds: Maximum runtime in seconds (default: 3600)
            - cpu: CPU cores allocated (default: 1.0)
            - memory: Memory in MB allocated (default: 1024)
            - secrets: Dictionary of environment variables to inject (creates new secret)
            - volumes: Dictionary of volumes to mount in sandbox, where the key is the path in the sandbox and the value is the name of the volume
            - workdir: Working directory in sandbox (default: "/")
            - gpu_type: Type of GPU to use (optional). Supported types:
              * T4: Entry-level GPU, good for inference
              * L4: Mid-range GPU, good for general ML tasks
              * A10G: High-performance GPU, good for training
              * A100-40GB: High-end GPU with 40GB memory
              * A100-80GB: High-end GPU with 80GB memory
              * L40S: Latest generation GPU, good for ML workloads
              * H100: Latest generation high-end GPU
              * H200: Latest generation flagship GPU
              * B200: Latest generation enterprise GPU
            - gpu_count: Number of GPUs to use (optional, default: 1)
              * A10G supports up to 4 GPUs
              * Other types support up to 8 GPUs
            
            Returns a SandboxLaunchResponse containing:
            - sandbox_id: Unique identifier for the sandbox
            - status: Current status of the sandbox
            - python_version: Python version installed
            - pip_packages: List of pip packages installed
            - apt_packages: List of apt packages installed
            - preloaded_secrets: List of predefined secrets injected from Modal dashboard
            
            This tool is useful for:
            - Creating isolated Python environments
            - Running code with specific dependencies
            - Testing in clean environments
            - Executing long-running tasks
            - Running GPU-accelerated workloads
            - Training machine learning models
            - Running inference on large models
            
            Secrets Management:
            - Use 'secrets' parameter to create new secrets with key-value pairs
            - Use 'inject_predefined_secrets' to reference existing secrets from Modal dashboard
            - Predefined secrets are applied after custom secrets, so they can override values
            - Access secrets as environment variables in your sandbox code using os.environ
            """

    TERMINATE_SANDBOX = """
            Terminates a Modal sandbox by its ID.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox to terminate
            
            Returns a SandboxTerminateResponse containing:
            - success: Boolean indicating if termination was successful
            - message: Detailed message about the termination result
            
            This tool is useful for:
            - Stopping running sandboxes that are no longer needed
            - Cleaning up resources
            - Forcefully ending long-running or stuck sandboxes
            - Managing sandbox lifecycle
            
            The tool will:
            1. Check if the sandbox exists and is running
            2. Send termination signal if running
            3. Wait for confirmation of termination
            4. Return status of the operation
            """

    LIST_SANDBOXES = """
            Lists all Modal sandboxes for a specific app namespace and their current status.
            
            Parameters:
            - app_name: Name of the Modal app namespace to list sandboxes for
            
            Returns a list of sandboxes containing:
            - sandbox_id: Unique identifier for each sandbox
            - sandbox_status: Current state of the sandbox (running/stopped)
            
            This tool is useful for:
            - Monitoring active Modal sandbox environments within an app namespace
            - Checking which sandboxes are currently running
            - Getting sandbox IDs for further management operations
            """

    EXECUTE_COMMAND = """
            Executes a command in a specified Modal sandbox environment.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox to run the command in
            - command: The shell command to execute (e.g. "python script.py", "ls -la", etc.)
            - working_dir: Optional working directory to execute the command from
            - timeout: Optional timeout in seconds for command execution
            
            Returns a SandboxExecuteResponse containing:
            - stdout: Standard output from the command execution
            - stderr: Standard error output from the command execution  
            - returncode: Exit code of the command (0 typically indicates success)
            - execution_time: Time taken to execute the command in seconds
            
            This tool is useful for:
            - Running arbitrary commands in isolated sandbox environments
            - Testing scripts and programs in clean environments
            - Executing programs with specific dependencies
            - Debugging environment-specific issues
            - Running automated tests in isolation
            
            The tool will:
            1. Verify the sandbox exists and is running
            2. Execute the specified command in that sandbox
            3. Capture all output and timing information
            4. Return detailed execution results
            """


    PUSH_FILE_TO_SANDBOX = """
            Copies a file from the local filesystem to a Modal sandbox.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - local_path: Path to the source file on local filesystem
            - sandbox_path: Destination path in the sandbox
            - read_file_mode: Optional mode for reading local file (default: "rb")
            - writefile_mode: Optional mode for writing to sandbox (default: "wb")
            
            Returns a PushFileToSandboxResponse containing:
            - success: Boolean indicating if copy was successful
            - message: Descriptive message about the copy operation
            - local_path: The source path on local filesystem
            - sandbox_path: The destination path in sandbox
            - file_size: Size of the file in bytes
            
            This tool is useful for:
            - Uploading input files to sandboxes
            - Transferring configuration files
            - Setting up sandbox environments
            - Deploying code to sandboxes
            
            The tool will:
            1. Verify sandbox is running and local file exists
            2. Read contents from local file
            3. Write contents to sandbox path
            4. Return status of the operation
            """

    PULL_FILE_FROM_SANDBOX = """
            Copies a file from a Modal sandbox to the local filesystem.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - sandbox_path: Path to the file in the sandbox
            - local_path: Destination path on local filesystem
            
            Returns a PullFileFromSandboxResponse containing:
            - success: Boolean indicating if copy was successful
            - message: Descriptive message about the copy operation
            - sandbox_path: The source path in sandbox
            - local_path: The destination path on local filesystem
            - file_size: Size of the file in bytes
           
            
            This tool is useful for:
            - Retrieving output files from sandbox executions
            - Backing up sandbox data
            - Analyzing sandbox-generated content locally
            - Debugging sandbox operations
            
            The tool will:
            1. Verify sandbox and source file exist
            2. Create local destination directory if needed
            3. Copy file contents from sandbox to local system
            4. Return status of the operation
            """

    LIST_DIRECTORY_CONTENTS = """
            Lists contents of a directory in the sandbox.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - path: Directory path to list in the sandbox
            
            Returns a SandboxListDirectoryResponse containing:
            - contents: List of filenames/directories at the specified path
            
            This tool is useful for:
            - Exploring sandbox filesystem structure
            - Verifying file operations
            - Debugging file-related issues
            - Managing sandbox content
            
            The tool will:
            1. Verify sandbox and directory exist
            2. List all contents at specified path
            3. Return directory listing
            """

    MAKE_DIRECTORY = """
            Creates a new directory in the sandbox.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - path: Directory path to create in the sandbox
            - parents: Whether to create parent directories if they don't exist
            
            Returns a SandboxMakeDirectoryResponse containing:
            - success: Boolean indicating if directory creation was successful
            - message: Descriptive message about the operation
            - path_created: The path that was created
           
            
            This tool is useful for:
            - Setting up directory structures
            - Preparing for file operations
            - Organizing sandbox content
            
            The tool will:
            1. Verify sandbox exists and is running
            2. Create directory at specified path
            3. Return status of the operation
            """

    REMOVE_PATH = """
            Removes a file or directory from the sandbox.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - path: Path to remove from the sandbox
            - recursive: Whether to remove the path recursively
            
            Returns a SandboxRemovePathResponse containing:
            - success: Boolean indicating if removal was successful
            - message: Descriptive message about the operation
            - path_removed: The path that was removed
           
            
            This tool is useful for:
            - Cleaning up temporary files
            - Removing unwanted content
            - Managing sandbox storage
            
            The tool will:
            1. Verify sandbox exists and is running
            2. Remove specified path (file or directory)
            3. Return status of the operation
            """

    READ_FILE_CONTENT_FROM_SANDBOX = """
            Reads the content of a file in the sandbox.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - path: Path to the file to read
            
            Returns a SandboxReadFileContentResponse containing:
            - content: String content of the file
            
            This tool is useful for:
            - Viewing file contents without downloading
            - Debugging sandbox operations
            - Checking operation results
            - Quick file inspection
            
            The tool will:
            1. Verify sandbox and file exist
            2. Read file contents
            3. Return file content as string
            """

    WRITE_FILE_CONTENT_TO_SANDBOX = """
            Writes content to a file in a Modal sandbox.
            This is useful for writing code, text, or any other content to a file in the sandbox.

            Parameters:
            - sandbox_id: ID of the target sandbox where code will be written
            - sandbox_path: Path where the code file should be created/written in the sandbox
            - content: Content to write to the file

            Returns a SandboxWriteCodeResponse containing:
            - success: Boolean indicating if code was written successfully
            - message: Descriptive message about the operation
            - file_path: Path where code was written in sandbox

            This tool is powerful for:
            - Rapid prototyping and code generation
            - Creating boilerplate code
            - Implementing algorithms from descriptions
            - Converting pseudocode to actual code
            - Generating test cases
            - Creating utility functions and helper code

            The tool will:
            1. Verify the sandbox is running
            2. Write content to specified path in sandbox
            3. Handle errors and provide detailed feedback

            """

    PUSH_MULTIPLE_FILES_TO_SANDBOX = """
            Copies multiple files matching a glob pattern from the local filesystem to a Modal sandbox.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - local_base_path: Base directory path on local filesystem to search for files
            - sandbox_base_path: Base directory path in sandbox where files will be copied
            - glob_pattern: Glob pattern to match files (e.g., "*.py", "**/*.txt", "src/**/*")
            - read_file_mode: Optional mode for reading local files (default: "rb")
            - writefile_mode: Optional mode for writing to sandbox (default: "wb")
            - concurrency_limit: Maximum number of concurrent file transfers (default: 10)
            
            Returns a PushMultipleFilesToSandboxResponse containing:
            - success: Boolean indicating if all copy operations were successful
            - message: Descriptive message about the copy operations
            - local_base_path: The base path on local filesystem
            - sandbox_base_path: The base path in sandbox
            - glob_pattern: The pattern used to match files
            - files_transferred: List of file transfer details (local_path, sandbox_path, file_size)
            - total_files: Number of files transferred
            - total_size: Total size of all files transferred in bytes
            
            This tool is useful for:
            - Bulk uploading project files to sandboxes
            - Transferring entire directory structures
            - Deploying codebases with specific file patterns
            - Uploading datasets with filtering
            - Setting up complex sandbox environments
            
            Performance tuning:
            - Increase concurrency_limit for faster transfers on high-bandwidth connections
            - Decrease concurrency_limit to reduce system load or API rate limiting
            - Default of 10 provides good balance for most use cases
            
            The tool will:
            1. Verify sandbox is running and local base path exists
            2. Find all files matching the glob pattern in local base path
            3. Preserve directory structure when copying to sandbox
            4. Transfer each file and track success/failure
            5. Return comprehensive status of all operations
            """

    PULL_MULTIPLE_FILES_FROM_SANDBOX = """
            Copies multiple files matching a glob pattern from a Modal sandbox to the local filesystem.
            
            Parameters:
            - sandbox_id: The unique identifier of the sandbox
            - sandbox_base_path: Base directory path in sandbox to search for files
            - local_base_path: Base directory path on local filesystem where files will be copied
            - glob_pattern: Glob pattern to match files (e.g., "*.py", "**/*.txt", "output/**/*")
            - concurrency_limit: Maximum number of concurrent file transfers (default: 10)
            
            Returns a PullMultipleFilesFromSandboxResponse containing:
            - success: Boolean indicating if all copy operations were successful
            - message: Descriptive message about the copy operations
            - sandbox_base_path: The base path in sandbox
            - local_base_path: The base path on local filesystem
            - glob_pattern: The pattern used to match files
            - files_transferred: List of file transfer details (sandbox_path, local_path, file_size)
            - total_files: Number of files transferred
            - total_size: Total size of all files transferred in bytes
            
            This tool is useful for:
            - Bulk downloading results from sandbox executions
            - Backing up entire sandbox directories
            - Retrieving generated datasets or outputs
            - Downloading logs and artifacts
            - Analyzing sandbox-generated content locally
            
            Performance tuning:
            - Increase concurrency_limit for faster transfers on high-bandwidth connections
            - Decrease concurrency_limit to reduce system load or API rate limiting
            - Default of 10 provides good balance for most use cases
            
            The tool will:
            1. Verify sandbox exists and sandbox base path is accessible
            2. Find all files matching the glob pattern in sandbox base path
            3. Create local directory structure as needed
            4. Transfer each file and track success/failure
            5. Return comprehensive status of all operations
            """