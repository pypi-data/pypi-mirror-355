from pydantic import BaseModel
from typing import List, Dict, Optional, Any 

from enum import Enum 

class SandboxStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"

class SandboxListItem(BaseModel):
    sandbox_id: str
    sandbox_status: SandboxStatus

class SandboxLaunchResponse(BaseModel):
    sandbox_id: str
    status: str
    python_version: str
    pip_packages: List[str]
    apt_packages: List[str]
    preloaded_secrets: List[str] = []

class SandboxTerminateResponse(BaseModel):
    success: bool
    message: str

class SandboxExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    returncode: int
    execution_time: float


class SandboxReadFileContentResponse(BaseModel):
    content: str

class SandboxListDirectoryContentsResponse(BaseModel):
    contents: List[str]

class SandboxMakeDirectoryResponse(BaseModel):
    success: bool
    message: str
    path_created: str
   
class SandboxRemovePathResponse(BaseModel):
    success: bool
    message: str
    path_removed: str

class PushFileToSandboxResponse(BaseModel):
    success: bool
    message: str
    local_path: str
    sandbox_path: str
    file_size: int
   
class PullFileFromSandboxResponse(BaseModel):
    success: bool
    message: str
    sandbox_path: str
    local_path: str
    file_size: int

class SandboxWriteFileResponse(BaseModel):
    success: bool
    message: str
    file_path: str

class PushMultipleFilesToSandboxResponse(BaseModel):
    success: bool
    message: str
    local_base_path: str
    sandbox_base_path: str
    glob_pattern: str
    files_transferred: List[Dict[str, Any]]  # List of {local_path, sandbox_path, file_size}
    total_files: int
    total_size: int

class PullMultipleFilesFromSandboxResponse(BaseModel):
    success: bool
    message: str
    sandbox_base_path: str
    local_base_path: str
    glob_pattern: str
    files_transferred: List[Dict[str, Any]]  # List of {sandbox_path, local_path, file_size}
    total_files: int
    total_size: int
