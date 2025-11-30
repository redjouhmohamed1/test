"""
Code execution tool for the AI Agent
"""

import asyncio
import subprocess
import tempfile
import os
from typing import Dict, Any
from ..core.base import BaseTool


class CodeExecutorTool(BaseTool):
    """Tool for executing code in various languages"""
    
    def __init__(self):
        super().__init__(
            name="code_executor",
            description="Execute code in Python, JavaScript, or Bash"
        )
        
        self.supported_languages = {
            "python": {
                "extension": ".py",
                "command": ["python3"],
                "timeout": 30
            },
            "javascript": {
                "extension": ".js",
                "command": ["node"],
                "timeout": 30
            },
            "bash": {
                "extension": ".sh",
                "command": ["bash"],
                "timeout": 30
            }
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute code"""
        code = parameters.get("code", "")
        language = parameters.get("language", "python").lower()
        timeout = parameters.get("timeout", 30)
        
        if not code:
            return {"error": "No code provided"}
        
        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}. Supported: {list(self.supported_languages.keys())}"}
        
        try:
            result = await self._execute_code(code, language, timeout)
            return result
        except Exception as e:
            return {"error": f"Execution failed: {str(e)}"}
    
    async def _execute_code(self, code: str, language: str, timeout: int) -> Dict[str, Any]:
        """Execute code in a temporary file"""
        lang_config = self.supported_languages[language]
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=lang_config["extension"],
            delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name
        
        try:
            # Prepare command
            command = lang_config["command"] + [temp_file_path]
            
            # Execute code
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tempfile.gettempdir()
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                return {
                    "code": code,
                    "language": language,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8'),
                    "return_code": process.returncode,
                    "success": process.returncode == 0
                }
                
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "code": code,
                    "language": language,
                    "error": f"Execution timed out after {timeout} seconds",
                    "success": False
                }
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool"""
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The code to execute"
                },
                "language": {
                    "type": "string",
                    "description": "Programming language",
                    "enum": list(self.supported_languages.keys()),
                    "default": "python"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                }
            },
            "required": ["code"],
            "examples": [
                {
                    "code": "print('Hello, World!')",
                    "language": "python"
                },
                {
                    "code": "console.log('Hello, World!');",
                    "language": "javascript"
                },
                {
                    "code": "echo 'Hello, World!'",
                    "language": "bash"
                }
            ]
        }