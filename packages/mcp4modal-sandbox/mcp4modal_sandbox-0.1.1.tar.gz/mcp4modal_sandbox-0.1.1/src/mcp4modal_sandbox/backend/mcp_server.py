import os
import glob
import fnmatch
import asyncio
import aiofiles
from os import path, makedirs
from time import time 

import modal 
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from contextlib import asynccontextmanager

from typing import List, Dict, Optional, Type 
from typing import Self
from enum import Enum

from concurrent.futures import ThreadPoolExecutor

from mcp4modal_sandbox.log import logger
from mcp4modal_sandbox.settings import MCPServerSettings
from mcp4modal_sandbox.backend.mcp_metadata import MCP_NAME, MCP_INSTRUCTIONS
from mcp4modal_sandbox.backend.tool_descriptions import ToolDescriptions
from mcp4modal_sandbox.backend.response_schema import (
    SandboxStatus,
    SandboxListItem,
    SandboxLaunchResponse,
    SandboxTerminateResponse,
    SandboxExecuteResponse,
    PushFileToSandboxResponse,
    PullFileFromSandboxResponse,
    SandboxListDirectoryContentsResponse,
    SandboxMakeDirectoryResponse,
    SandboxRemovePathResponse,
    SandboxReadFileContentResponse,
    SandboxWriteFileResponse,
    PushMultipleFilesToSandboxResponse,
    PullMultipleFilesFromSandboxResponse,
)


class GPUType(str, Enum):
    T4 = "T4"
    L4 = "L4"
    A10G = "A10G"
    A100_40GB = "A100-40GB"
    A100_80GB = "A100-80GB"
    L40S = "L40S"
    H100 = "H100"
    H200 = "H200"
    B200 = "B200"

    @classmethod
    def get_max_gpu_count(cls, gpu_type: 'GPUType') -> int:
        if gpu_type == cls.A10G:
            return 4
        return 8

    
class MCPServer:
    def __init__(self, app_name:str, settings: MCPServerSettings, preloaded_secrets:List[str] = None, max_workers:int = 64):
        self.settings = settings
        self.app_name = app_name
        self.preloaded_secrets = preloaded_secrets
        self.max_workers = max_workers

    async def run_mcp(self, transport: str = 'stdio'):
        match transport:
            case 'stdio':
                await self.mcp_app.run_async(transport=transport)
            case 'streamable-http' | 'sse':
                await self.mcp_app.run_async(transport=transport, host=self.settings.mcp_host, port=self.settings.mcp_port)
            case _:
                raise ValueError(f"Invalid transport: {transport}. Must be one of: stdio, streamable-http, sse")
        
    async def __aenter__(self) -> Self:
        self.mcp_app = FastMCP(
            name=MCP_NAME,
            instructions=MCP_INSTRUCTIONS,
        )
        await self.register_tools(self.mcp_app)
        logger.info('MCPServer initialized')
        self.thread_pool_executor = ThreadPoolExecutor(max_workers=self.max_workers)
        return self
 
        
    async def __aexit__(self, exc_type: Optional[Type[Exception]], exc_value: Optional[Exception], traceback: Optional[str]) -> None:
        if exc_type is not None:
            logger.error(f"SandboxManager exited with exception: {exc_type} {exc_value}")
            logger.exception(traceback)
        
        logger.info('SandboxManager exited') 
        self.thread_pool_executor.shutdown(wait=True)

    async def _read_sandbox_file_in_thread(self, modal_sandbox, file_path: str, mode: str = 'rb'):
        def _sync_read():
            with modal_sandbox.open(file_path, mode) as f:
                return f.read()
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool_executor, _sync_read)

    async def _write_sandbox_file_in_thread(self, modal_sandbox, file_path: str, content, mode: str = 'wb'):
        def _sync_write():
            with modal_sandbox.open(file_path, mode) as f:
                f.write(content)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool_executor, _sync_write)

    async def register_tools(self, mcp_app:FastMCP):
        mcp_app.tool(
            name="launch_sandbox",
            description=ToolDescriptions.LAUNCH_SANDBOX,
        )(self.launch_sandbox)

        mcp_app.tool(
            name="terminate_sandbox", 
            description=ToolDescriptions.TERMINATE_SANDBOX,
        )(self.terminate_sandbox)

        mcp_app.tool(
            name="list_sandboxes",
            description=ToolDescriptions.LIST_SANDBOXES,
        )(self.list_sandboxes)

        mcp_app.tool(
            name="execute_command",
            description=ToolDescriptions.EXECUTE_COMMAND,
        )(self.execute_command)

        mcp_app.tool(
            name="push_file_to_sandbox",
            description=ToolDescriptions.PUSH_FILE_TO_SANDBOX,
        )(self.push_file_to_sandbox)

        mcp_app.tool(
            name="pull_file_from_sandbox",
            description=ToolDescriptions.PULL_FILE_FROM_SANDBOX,
        )(self.pull_file_from_sandbox)

        mcp_app.tool(
            name="list_directory_contents",
            description=ToolDescriptions.LIST_DIRECTORY_CONTENTS,
        )(self.list_directory_contents)

        mcp_app.tool(
            name="make_directory",
            description=ToolDescriptions.MAKE_DIRECTORY,
        )(self.make_directory)

        mcp_app.tool(
            name="remove_path",
            description=ToolDescriptions.REMOVE_PATH,
        )(self.remove_path)

        mcp_app.tool(
            name="read_file_content_from_sandbox",
            description=ToolDescriptions.READ_FILE_CONTENT_FROM_SANDBOX,
        )(self.read_file_content_from_sandbox)

        mcp_app.tool(
            name="write_file_content_to_sandbox",
            description=ToolDescriptions.WRITE_FILE_CONTENT_TO_SANDBOX,
        )(self.write_file_content_to_sandbox)

        mcp_app.tool(
            name="push_multiple_files_to_sandbox",
            description=ToolDescriptions.PUSH_MULTIPLE_FILES_TO_SANDBOX,
        )(self.push_multiple_files_to_sandbox)

        mcp_app.tool(
            name="pull_multiple_files_from_sandbox",
            description=ToolDescriptions.PULL_MULTIPLE_FILES_FROM_SANDBOX,
        )(self.pull_multiple_files_from_sandbox)


        

    async def list_sandboxes(self, ctx:Context) -> List[SandboxListItem]:
        await ctx.info(f"Listing sandboxes for app '{self.app_name}'...")
        app = modal.App.lookup(self.app_name, create_if_missing=True)
        sandbox_list: List[SandboxListItem] = []
        async for sandbox in modal.Sandbox.list.aio(app_id=app.app_id):
            sandbox_status = await sandbox.poll.aio()
            sandbox_list.append(SandboxListItem(
                sandbox_id=sandbox.object_id,
                sandbox_status=SandboxStatus.RUNNING if sandbox_status is None else SandboxStatus.STOPPED,
            ))
        await ctx.info(f"Found {len(sandbox_list)} sandboxes")
        return sandbox_list
    
    async def launch_sandbox(
        self, 
        python_version: str = "3.12",
        pip_packages: List[str] = None,
        apt_packages: List[str] = None,
        timeout_seconds: int = 600,
        cpu: float = 2.0,
        memory: int = 4096,
        secrets: Dict[str, str] = None,
        volumes: Dict[str, str] = None,
        workdir: str = "/home/solver",
        gpu_type: Optional[GPUType] = None,
        gpu_count: Optional[int] = None,
    ) -> SandboxLaunchResponse:
        pip_packages = pip_packages or []
        apt_packages = apt_packages or []
        secrets = secrets or {}
        inject_predefined_secrets = self.preloaded_secrets or []

        # Build the image with Python version and dependencies
        image = modal.Image.debian_slim(python_version=python_version)
        
        # Install system dependencies
        if apt_packages:
            image = image.apt_install(*apt_packages)
        
        # Install Python packages
        if pip_packages:
            image = image.pip_install(*pip_packages)
        
        # Create secrets for environment variables (the proper Modal way)
        modal_secrets = []
        if secrets:
            secret = modal.Secret.from_dict(secrets)
            modal_secrets.append(secret)
        
        if inject_predefined_secrets:
            for secret_name in inject_predefined_secrets:
                secret = modal.Secret.from_name(secret_name)
                modal_secrets.append(secret)
        
        modal_volumes = {}
        if volumes:
            for volume_path, volume_name in volumes.items():
                modal_volumes[volume_path] = modal.Volume.from_name(volume_name, create_if_missing=True)
        
        # Configure GPU if specified
        gpu = None
        if gpu_type:
            if gpu_count:
                max_gpus = GPUType.get_max_gpu_count(gpu_type)
                if gpu_count > max_gpus:
                    raise ToolError(f"{gpu_type.value} supports up to {max_gpus} GPUs")
                gpu = f"{gpu_type.value}:{gpu_count}"
            else:
                gpu = gpu_type.value
        
        # Get or create Modal app for the specified namespace
        app = modal.App.lookup(self.app_name, create_if_missing=True)
        
        # Create sandbox with Modal
        with modal.enable_output():
            logger.info(f"Creating sandbox with Python {python_version} in app '{self.app_name}'" + (f" and GPU {gpu}" if gpu else ""))
            sandbox = await modal.Sandbox.create.aio(
                "/bin/bash",
                image=image,
                app=app,
                timeout=timeout_seconds,
                cpu=cpu,
                memory=memory,
                secrets=modal_secrets,
                volumes=modal_volumes,
                workdir=workdir,
                gpu=gpu
            )
            
        # Get the Modal-assigned ID
        sandbox_id = sandbox.object_id
        
        logger.info(f"Launched sandbox {sandbox_id} with Python {python_version}")
        
        return SandboxLaunchResponse(
            sandbox_id=sandbox_id,
            status="running",
            python_version=python_version,
            pip_packages=pip_packages,
            apt_packages=apt_packages,
            preloaded_secrets=inject_predefined_secrets,
        )
    

    async def terminate_sandbox(self, sandbox_id: str) -> SandboxTerminateResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)

        # Check if sandbox is running before terminating
        sandbox_status = await modal_sandbox.poll.aio()
        
        # Terminate the Modal sandbox
        if sandbox_status is not None:
            return SandboxTerminateResponse(
                success=False,
                message=f"Sandbox {sandbox_id} is not running"
            )
        
        await modal_sandbox.terminate.aio()
        
        # Wait for termination
        await modal_sandbox.wait.aio(raise_on_termination=False)
        
        logger.info(f"Terminated sandbox {sandbox_id}")
        
        return SandboxTerminateResponse(
            success=True,
            message=f"Sandbox {sandbox_id} terminated successfully"
        )
    

    async def execute_command(
        self,
        sandbox_id: str, 
        command: List[str],
        timeout_seconds: int = 30
    ) -> SandboxExecuteResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        
        # Check if sandbox is running before executing command
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        start_time = time()
        
        result = await modal_sandbox.exec.aio(*command, timeout=timeout_seconds)
        await result.wait.aio()
        
        execution_time = time() - start_time
        # Get output from the sandbox
        stdout = result.stdout.read() if result.stdout else ""
        stderr = result.stderr.read() if result.stderr else ""
        returncode = result.returncode
        
        logger.info(f"Executed command in sandbox {sandbox_id}: {' '.join(command)}")
        
        return SandboxExecuteResponse(
            stdout=stdout,
            stderr=stderr,
            returncode=returncode,
            execution_time=execution_time
        )

    async def push_file_to_sandbox(
        self, 
        sandbox_id: str, 
        local_path: str, 
        sandbox_path: str,
        read_file_mode: str = "rb",
        writefile_mode: str = "wb"
    ) -> PushFileToSandboxResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        
        # Check if sandbox is running before copying file
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        if not path.exists(local_path):
            raise ToolError(f"Local file {local_path} does not exist")
        
        # Get file size
        file_size = os.path.getsize(local_path)
        
        # Read local file asynchronously
        async with aiofiles.open(local_path, read_file_mode) as file_pointer:
            content = await file_pointer.read()
        
        # Write to sandbox using thread executor
        await self._write_sandbox_file_in_thread(modal_sandbox, sandbox_path, content, writefile_mode)
        
        logger.info(f"Copied file from {local_path} to {sandbox_path} in sandbox {sandbox_id}")
        
        return PushFileToSandboxResponse(
            success=True,
            message=f"File copied successfully to {sandbox_path}",
            local_path=local_path,
            sandbox_path=sandbox_path,
            file_size=file_size,
        )

    async def list_directory_contents(self, sandbox_id: str, path: str) -> SandboxListDirectoryContentsResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        
        # Check if sandbox is running before listing directory
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        contents = await modal_sandbox.ls.aio(path)
        logger.info(f"Listed directory {path} in sandbox {sandbox_id}")
        
        return SandboxListDirectoryContentsResponse(
            contents=contents
        )

    async def make_directory(self, sandbox_id: str, path: str, parents: bool = False) -> SandboxMakeDirectoryResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
    
        # Check if sandbox is running before creating directory
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        await modal_sandbox.mkdir.aio(path, parents=parents)
        logger.info(f"Created directory {path} in sandbox {sandbox_id}")
        
        return SandboxMakeDirectoryResponse(
            success=True,
            message=f"Directory {path} created successfully",
            path_created=path,
        )

    async def remove_path(self, sandbox_id: str, path: str, recursive: bool = False) -> SandboxRemovePathResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)    
        await modal_sandbox.rm.aio(path, recursive=recursive)
        
        logger.info(f"Removed path {path} in sandbox {sandbox_id}")
        
        return SandboxRemovePathResponse(
            success=True,
            message=f"Path {path} removed successfully",
            path_removed=path,
        )

    async def pull_file_from_sandbox(
        self, 
        sandbox_id: str, 
        sandbox_path: str, 
        local_path: str
    ) -> PullFileFromSandboxResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
    
        # Check if sandbox is running before copying file from sandbox
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        # Read from sandbox using thread executor
        content = await self._read_sandbox_file_in_thread(modal_sandbox, sandbox_path, 'rb')
        
        file_size = len(content)
        
        # Write to local file asynchronously
        makedirs(path.dirname(local_path), exist_ok=True)
        async with aiofiles.open(local_path, 'wb') as file_pointer:
            await file_pointer.write(content)
        
        logger.info(f"Copied file from {sandbox_path} to {local_path} from sandbox {sandbox_id}")
        
        return PullFileFromSandboxResponse(
            success=True,
            message=f"File copied successfully to {local_path}",
            file_size=file_size,
            sandbox_path=sandbox_path,
            local_path=local_path,
        )

    async def read_file_content_from_sandbox(self, sandbox_id: str, path: str) -> SandboxReadFileContentResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        
        # Check if sandbox is running before reading file
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        # Read from sandbox using thread executor
        content = await self._read_sandbox_file_in_thread(modal_sandbox, path, 'rb')
        
        logger.info(f"Read file content from {path} in sandbox {sandbox_id}")
        
        return SandboxReadFileContentResponse(
            content=content
        )
    
    async def write_file_content_to_sandbox(
            self, 
            sandbox_id:str, 
            sandbox_path:str,
            content:str,
            ) -> SandboxWriteFileResponse:
        sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        sandbox_status = await sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        # Write to sandbox using thread executor
        await self._write_sandbox_file_in_thread(sandbox, sandbox_path, content, "w")

        logger.info(f"Content written successfully to {sandbox_path}")

        return SandboxWriteFileResponse(
            success=True,
            message=f"Content written successfully to {sandbox_path}",
            file_path=sandbox_path,
        )

    async def push_multiple_files_to_sandbox(
        self,
        sandbox_id: str,
        local_base_path: str,
        sandbox_base_path: str, 
        glob_pattern: str,
        read_file_mode: str = "rb",
        writefile_mode: str = "wb",
        concurrency_limit: int = 10
    ) -> PushMultipleFilesToSandboxResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        
        # Check if sandbox is running
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        # Verify local base path exists
        if not path.exists(local_base_path):
            raise ToolError(f"Local base path {local_base_path} does not exist")
        
        # Find all files matching the glob pattern
        search_pattern = path.join(local_base_path, glob_pattern)
        matched_files = glob.glob(search_pattern, recursive=True)
        
        # Filter to only include files (not directories)
        file_list = [f for f in matched_files if path.isfile(f)]
        
        if not file_list:
            return PushMultipleFilesToSandboxResponse(
                success=True,
                message=f"No files found matching pattern '{glob_pattern}' in {local_base_path}",
                local_base_path=local_base_path,
                sandbox_base_path=sandbox_base_path,
                glob_pattern=glob_pattern,
                files_transferred=[],
                total_files=0,
                total_size=0
            )
        
        # Ensure sandbox base path exists
        try:
            await modal_sandbox.ls.aio(sandbox_base_path)
        except:
            await modal_sandbox.mkdir.aio(sandbox_base_path, parents=True)

        # Use semaphore to limit concurrent transfers (avoid overwhelming Modal API)
        semaphore = asyncio.Semaphore(concurrency_limit)
        mutex = asyncio.Lock()
        
        # Create transfer tasks for all files
        transfer_tasks = [
            self._push_single_file_to_sandbox(
                modal_sandbox, local_file_path, local_base_path, sandbox_base_path,
                read_file_mode, writefile_mode, semaphore, mutex
            )
            for local_file_path in file_list
        ]
        
        # Execute all transfers concurrently
        transfer_results = await asyncio.gather(*transfer_tasks, return_exceptions=True)
        
        # Process results
        files_transferred = []
        failed_transfers = []
        total_size = 0
        
        for result in transfer_results:
            if isinstance(result, Exception):
                failed_transfers.append({
                    "local_path": "unknown",
                    "error": str(result)
                })
            elif result.get("success"):
                files_transferred.append({
                    "local_path": result["local_path"],
                    "sandbox_path": result["sandbox_path"],
                    "file_size": result["file_size"]
                })
                total_size += result["file_size"]
            else:
                failed_transfers.append({
                    "local_path": result["local_path"],
                    "error": result["error"]
                })
        
        success = len(failed_transfers) == 0
        total_transferred = len(files_transferred)
        
        if failed_transfers:
            failed_count = len(failed_transfers)
            message = f"Transferred {total_transferred} files successfully, {failed_count} files failed"
        else:
            message = f"Successfully transferred {total_transferred} files ({total_size} bytes)"
        
        logger.info(f"Pushed {total_transferred} files to sandbox {sandbox_id} using pattern '{glob_pattern}'")
        
        return PushMultipleFilesToSandboxResponse(
            success=success,
            message=message,
            local_base_path=local_base_path,
            sandbox_base_path=sandbox_base_path,
            glob_pattern=glob_pattern,
            files_transferred=files_transferred,
            total_files=total_transferred,
            total_size=total_size
        )

    async def _push_single_file_to_sandbox(
        self,
        modal_sandbox:modal.Sandbox,
        local_file_path: str,
        local_base_path: str,
        sandbox_base_path: str,
        read_file_mode: str,
        writefile_mode: str,
        semaphore: asyncio.Semaphore,
        mutex: asyncio.Lock
    ) -> dict:
        async with semaphore:  # Limit concurrent transfers
            try:
                # Calculate relative path from base
                relative_path = path.relpath(local_file_path, local_base_path)
                sandbox_file_path = path.join(sandbox_base_path, relative_path).replace('\\', '/')
                
                # Get file size
                file_size = os.path.getsize(local_file_path)
                
                # Read local file asynchronously
                async with aiofiles.open(local_file_path, read_file_mode) as file_pointer:
                    content = await file_pointer.read()
                
                # Ensure directory exists in sandbox
                async with mutex:
                    sandbox_dir = path.dirname(sandbox_file_path)
                    if sandbox_dir and sandbox_dir != sandbox_base_path:
                        await modal_sandbox.mkdir.aio(sandbox_dir, parents=True)
                    
                # Write to sandbox using thread executor
                await self._write_sandbox_file_in_thread(modal_sandbox, sandbox_file_path, content, writefile_mode)
                
                return {
                    "success": True,
                    "local_path": local_file_path,
                    "sandbox_path": sandbox_file_path,
                    "file_size": file_size
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "local_path": local_file_path,
                    "error": str(e)
                }

    async def _pull_single_file_from_sandbox(
        self,
        modal_sandbox:modal.Sandbox,
        sandbox_file_path: str,
        sandbox_base_path: str,
        local_base_path: str,
        semaphore: asyncio.Semaphore,
        mutex: asyncio.Lock
    ) -> dict:
        async with semaphore:  # Limit concurrent transfers
            try:
                # Calculate relative path from sandbox base
                relative_path = sandbox_file_path[len(sandbox_base_path):].lstrip('/')
                local_file_path = path.join(local_base_path, relative_path)
                
                # Ensure local directory exists
                async with mutex:
                    local_dir = path.dirname(local_file_path)
                    if local_dir:
                        makedirs(local_dir, exist_ok=True)
                
                # Read from sandbox using thread executor
                content = await self._read_sandbox_file_in_thread(modal_sandbox, sandbox_file_path, 'rb')
                
                file_size = len(content)
                
                # Write to local file asynchronously
                async with aiofiles.open(local_file_path, 'wb') as file_pointer:
                    await file_pointer.write(content)
                
                return {
                    "success": True,
                    "sandbox_path": sandbox_file_path,
                    "local_path": local_file_path,
                    "file_size": file_size
                }
                
            except Exception as e:
                return {
                    "success": False,
                    "sandbox_path": sandbox_file_path,
                    "error": str(e)
                }

    async def pull_multiple_files_from_sandbox(
        self,
        sandbox_id: str,
        sandbox_base_path: str,
        local_base_path: str,
        glob_pattern: str,
        concurrency_limit: int = 10
    ) -> PullMultipleFilesFromSandboxResponse:
        # Get sandbox from Modal using from_id
        modal_sandbox = await modal.Sandbox.from_id.aio(sandbox_id)
        
        # Check if sandbox is running
        sandbox_status = await modal_sandbox.poll.aio()
        if sandbox_status is not None:
            raise ToolError(f"Sandbox {sandbox_id} is not running")
        
        # Get all files in the sandbox base path recursively
        try:
            all_files = await self._list_files_recursively(modal_sandbox, sandbox_base_path)
        except Exception as e:
            raise ToolError(f"Failed to list files in sandbox path {sandbox_base_path}: {str(e)}")
        
        # Filter files using glob pattern
        matching_files = []
        for file_path in all_files:
            # Calculate relative path from base
            if file_path.startswith(sandbox_base_path):
                relative_path = file_path[len(sandbox_base_path):].lstrip('/')
                if fnmatch.fnmatch(relative_path, glob_pattern) or fnmatch.fnmatch(file_path, glob_pattern):
                    matching_files.append(file_path)
        
        if not matching_files:
            return PullMultipleFilesFromSandboxResponse(
                success=True,
                message=f"No files found matching pattern '{glob_pattern}' in {sandbox_base_path}",
                sandbox_base_path=sandbox_base_path,
                local_base_path=local_base_path,
                glob_pattern=glob_pattern,
                files_transferred=[],
                total_files=0,
                total_size=0
            )
        
        # Ensure local base directory exists
        makedirs(local_base_path, exist_ok=True)
        
        # Use semaphore to limit concurrent transfers (avoid overwhelming Modal API)
        semaphore = asyncio.Semaphore(concurrency_limit)
        mutex = asyncio.Lock()
        # Create transfer tasks for all files
        transfer_tasks = [
            self._pull_single_file_from_sandbox(
                modal_sandbox, sandbox_file_path, sandbox_base_path, local_base_path, semaphore, mutex
            )
            for sandbox_file_path in matching_files
        ]
        
        # Execute all transfers concurrently
        transfer_results = await asyncio.gather(*transfer_tasks, return_exceptions=True)
        
        # Process results
        files_transferred = []
        failed_transfers = []
        total_size = 0
        
        for result in transfer_results:
            if isinstance(result, Exception):
                failed_transfers.append({
                    "sandbox_path": "unknown",
                    "error": str(result)
                })
            elif result.get("success"):
                files_transferred.append({
                    "sandbox_path": result["sandbox_path"],
                    "local_path": result["local_path"],
                    "file_size": result["file_size"]
                })
                total_size += result["file_size"]
            else:
                failed_transfers.append({
                    "sandbox_path": result["sandbox_path"],
                    "error": result["error"]
                })
        
        success = len(failed_transfers) == 0
        total_transferred = len(files_transferred)
        
        if failed_transfers:
            failed_count = len(failed_transfers)
            message = f"Transferred {total_transferred} files successfully, {failed_count} files failed"
        else:
            message = f"Successfully transferred {total_transferred} files ({total_size} bytes)"
        
        logger.info(f"Pulled {total_transferred} files from sandbox {sandbox_id} using pattern '{glob_pattern}'")
        
        return PullMultipleFilesFromSandboxResponse(
            success=success,
            message=message,
            sandbox_base_path=sandbox_base_path,
            local_base_path=local_base_path,
            glob_pattern=glob_pattern,
            files_transferred=files_transferred,
            total_files=total_transferred,
            total_size=total_size
        )

    async def _list_files_recursively(self, modal_sandbox:modal.Sandbox, directory_path: str) -> List[str]:
        all_files = []
        
        try:
            # Get directory contents
            contents = await modal_sandbox.ls.aio(directory_path)
            
            for item in contents:
                item_path = f"{directory_path.rstrip('/')}/{item}"
                
                try:
                    # Try to list as directory - if it succeeds, it's a directory
                    subdirectory_contents = await modal_sandbox.ls.aio(item_path)
                    # It's a directory, recurse into it
                    sub_files = await self._list_files_recursively(modal_sandbox, item_path)
                    all_files.extend(sub_files)
                except:
                    # It's a file, add it to the list
                    all_files.append(item_path)
                    
        except Exception as e:
            # If we can't list the directory, it might be a file or doesn't exist
            pass
            
        return all_files