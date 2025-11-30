"""
Calculator tool for the AI Agent
"""

import re
import math
import ast
import operator
from typing import Dict, Any
from ..core.base import BaseTool


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Perform mathematical calculations and solve equations"
        )
        
        # Safe operators for evaluation
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg,
        }
        
        # Safe functions
        self.functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'pi': math.pi,
            'e': math.e,
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """Execute mathematical calculation"""
        expression = parameters.get("expression", "")
        
        if not expression:
            return {"error": "No expression provided"}
        
        try:
            # Clean and validate expression
            cleaned_expr = self._clean_expression(expression)
            
            # Evaluate the expression safely
            result = self._safe_eval(cleaned_expr)
            
            return {
                "expression": expression,
                "cleaned_expression": cleaned_expr,
                "result": result,
                "type": type(result).__name__
            }
            
        except Exception as e:
            return {"error": f"Calculation failed: {str(e)}"}
    
    def _clean_expression(self, expression: str) -> str:
        """Clean and prepare expression for evaluation"""
        # Remove whitespace
        expr = expression.strip()
        
        # Replace common mathematical notation
        expr = expr.replace('^', '**')  # Power operator
        expr = expr.replace('×', '*')   # Multiplication
        expr = expr.replace('÷', '/')   # Division
        
        # Handle implicit multiplication (e.g., 2(3+4) -> 2*(3+4))
        expr = re.sub(r'(\d)\(', r'\1*(', expr)
        expr = re.sub(r'\)(\d)', r')*\1', expr)
        
        return expr
    
    def _safe_eval(self, expression: str) -> float:
        """Safely evaluate mathematical expression"""
        try:
            # Parse the expression into an AST
            node = ast.parse(expression, mode='eval')
            return self._eval_node(node.body)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")
    
    def _eval_node(self, node):
        """Recursively evaluate AST nodes"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op = self.operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(operand)
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name not in self.functions:
                raise ValueError(f"Unsupported function: {func_name}")
            args = [self._eval_node(arg) for arg in node.args]
            return self.functions[func_name](*args)
        elif isinstance(node, ast.Name):
            if node.id in self.functions:
                return self.functions[node.id]
            else:
                raise ValueError(f"Unsupported variable: {node.id}")
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool"""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sqrt(16)', 'sin(pi/2)')"
                }
            },
            "required": ["expression"],
            "examples": [
                "2 + 3 * 4",
                "sqrt(16) + 5",
                "sin(pi/2)",
                "log(10) + exp(1)",
                "(5 + 3) * 2 - 1"
            ]
        }