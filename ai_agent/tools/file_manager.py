"""
File management tool for the AI Agent
"""

import os
import aiofiles
from typing import Dict, Any
from ..core.base import BaseTool


class FileManagerTool(BaseTool):
    """Tool for file operations"""
    
    def __init__(self):
        super().__init__(
            name="file_manager",
            description="Read, write, and manage files"
        )
        
        self.allowed_extensions = {
            '.txt', '.py', '.js', '.json', '.csv', '.md', '.yaml', '.yml',
            '.xml', '.html', '.css', '.sql', '.log', '.conf', '.cfg'
        }
        
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute file operation"""
        operation = parameters.get("operation", "read")
        file_path = parameters.get("file_path", "")
        content = parameters.get("content", "")
        encoding = parameters.get("encoding", "utf-8")
        
        if not file_path:
            return {"error": "No file path provided"}
        
        # Security check - ensure file extension is allowed
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.allowed_extensions:
            return {"error": f"File extension '{file_ext}' not allowed. Allowed: {list(self.allowed_extensions)}"}
        
        # Security check - prevent path traversal
        if '..' in file_path or file_path.startswith('/'):
            return {"error": "Invalid file path. Relative paths only, no parent directory access."}
        
        try:
            if operation == "read":
                return await self._read_file(file_path, encoding)
            elif operation == "write":
                return await self._write_file(file_path, content, encoding)
            elif operation == "append":
                return await self._append_file(file_path, content, encoding)
            elif operation == "delete":
                return await self._delete_file(file_path)
            elif operation == "list":
                return await self._list_directory(file_path)
            elif operation == "exists":
                return await self._file_exists(file_path)
            else:
                return {"error": f"Unsupported operation: {operation}"}
                
        except Exception as e:
            return {"error": f"File operation failed: {str(e)}"}
    
    async def _read_file(self, file_path: str, encoding: str) -> Dict[str, Any]:
        """Read file content"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            return {"error": f"File too large: {file_size} bytes (max: {self.max_file_size})"}
        
        async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
            content = await f.read()
        
        return {
            "operation": "read",
            "file_path": file_path,
            "content": content,
            "size": file_size,
            "encoding": encoding
        }
    
    async def _write_file(self, file_path: str, content: str, encoding: str) -> Dict[str, Any]:
        """Write content to file"""
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        async with aiofiles.open(file_path, 'w', encoding=encoding) as f:
            await f.write(content)
        
        file_size = len(content.encode(encoding))
        
        return {
            "operation": "write",
            "file_path": file_path,
            "size": file_size,
            "encoding": encoding,
            "success": True
        }
    
    async def _append_file(self, file_path: str, content: str, encoding: str) -> Dict[str, Any]:
        """Append content to file"""
        async with aiofiles.open(file_path, 'a', encoding=encoding) as f:
            await f.write(content)
        
        file_size = os.path.getsize(file_path)
        
        return {
            "operation": "append",
            "file_path": file_path,
            "appended_size": len(content.encode(encoding)),
            "total_size": file_size,
            "encoding": encoding,
            "success": True
        }
    
    async def _delete_file(self, file_path: str) -> Dict[str, Any]:
        """Delete file"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        os.remove(file_path)
        
        return {
            "operation": "delete",
            "file_path": file_path,
            "success": True
        }
    
    async def _list_directory(self, dir_path: str) -> Dict[str, Any]:
        """List directory contents"""
        if not os.path.exists(dir_path):
            return {"error": f"Directory not found: {dir_path}"}
        
        if not os.path.isdir(dir_path):
            return {"error": f"Not a directory: {dir_path}"}
        
        items = []
        for item in os.listdir(dir_path):
            item_path = os.path.join(dir_path, item)
            is_dir = os.path.isdir(item_path)
            size = 0 if is_dir else os.path.getsize(item_path)
            
            items.append({
                "name": item,
                "type": "directory" if is_dir else "file",
                "size": size,
                "path": item_path
            })
        
        return {
            "operation": "list",
            "directory": dir_path,
            "items": items,
            "count": len(items)
        }
    
    async def _file_exists(self, file_path: str) -> Dict[str, Any]:
        """Check if file exists"""
        exists = os.path.exists(file_path)
        is_file = os.path.isfile(file_path) if exists else False
        is_dir = os.path.isdir(file_path) if exists else False
        
        result = {
            "operation": "exists",
            "file_path": file_path,
            "exists": exists,
            "is_file": is_file,
            "is_directory": is_dir
        }
        
        if exists:
            result["size"] = os.path.getsize(file_path) if is_file else 0
        
        return result
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool"""
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "File operation to perform",
                    "enum": ["read", "write", "append", "delete", "list", "exists"],
                    "default": "read"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to the file or directory"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write or append (required for write/append operations)"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding",
                    "default": "utf-8"
                }
            },
            "required": ["file_path"],
            "examples": [
                {
                    "operation": "read",
                    "file_path": "example.txt"
                },
                {
                    "operation": "write",
                    "file_path": "output.txt",
                    "content": "Hello, World!"
                },
                {
                    "operation": "list",
                    "file_path": "."
                }
            ]
        }