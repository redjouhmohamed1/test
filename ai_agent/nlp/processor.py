"""
Natural Language Processing module for the AI Agent
"""

import re
import json
import asyncio
from typing import Dict, List, Any, Optional
import openai
from openai import AsyncOpenAI

from ..core.base import BaseNLP, Message, ToolCall
from ..config.settings import agent_config
from ..utils.logger import setup_logger


class NLPProcessor(BaseNLP):
    """NLP processor using OpenAI's GPT models"""
    
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key
        self.model = model
        self.client = None
        self.system_prompt = agent_config.system_prompt
        self.logger = setup_logger(self.__class__.__name__)
        
        # Intent patterns
        self.intent_patterns = {
            "question": [r"\?", r"what", r"how", r"why", r"when", r"where", r"who"],
            "request": [r"please", r"can you", r"could you", r"would you"],
            "command": [r"do", r"make", r"create", r"generate", r"write"],
            "search": [r"search", r"find", r"look up", r"google"],
            "calculation": [r"calculate", r"compute", r"math", r"\+", r"-", r"\*", r"/"],
            "code": [r"code", r"program", r"script", r"function", r"class"],
            "file": [r"file", r"save", r"load", r"read", r"write", r"open"]
        }
        
        # Tool detection patterns
        self.tool_patterns = {
            "web_search": [r"search", r"google", r"find online", r"look up"],
            "calculator": [r"calculate", r"compute", r"math", r"solve", r"\d+[\+\-\*/]\d+"],
            "code_executor": [r"run code", r"execute", r"python", r"javascript"],
            "file_manager": [r"save file", r"read file", r"create file", r"open file"]
        }
    
    async def initialize(self):
        """Initialize the OpenAI client"""
        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.logger.info("OpenAI client initialized successfully")
        else:
            self.logger.warning("No OpenAI API key provided. Using fallback responses.")
    
    async def process_input(self, text: str) -> Dict[str, Any]:
        """Process input text and extract relevant information"""
        result = {
            "original_text": text,
            "intent": await self.extract_intent(text),
            "entities": await self._extract_entities(text),
            "requires_tools": False,
            "tool_requests": [],
            "sentiment": await self._analyze_sentiment(text),
            "complexity": self._assess_complexity(text)
        }
        
        # Check if tools are needed
        tool_requests = await self._detect_tool_needs(text)
        if tool_requests:
            result["requires_tools"] = True
            result["tool_requests"] = tool_requests
        
        return result
    
    async def extract_intent(self, text: str) -> Dict[str, Any]:
        """Extract intent from user input"""
        text_lower = text.lower()
        intent_scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            intent_scores[intent] = score
        
        # Get primary intent
        primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else "unknown"
        confidence = intent_scores.get(primary_intent, 0) / len(text.split()) if text.split() else 0
        
        return {
            "primary": primary_intent,
            "confidence": min(confidence, 1.0),
            "all_scores": intent_scores
        }
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text using simple patterns"""
        entities = []
        
        # Numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        for num in numbers:
            entities.append({"type": "number", "value": float(num), "text": num})
        
        # URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            entities.append({"type": "url", "value": url, "text": url})
        
        # Email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        for email in emails:
            entities.append({"type": "email", "value": email, "text": email})
        
        # File paths
        file_paths = re.findall(r'[./]?[\w/.-]+\.\w+', text)
        for path in file_paths:
            entities.append({"type": "file_path", "value": path, "text": path})
        
        return entities
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis"""
        positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "like", "happy", "pleased"]
        negative_words = ["bad", "terrible", "awful", "horrible", "hate", "dislike", "sad", "angry", "frustrated", "disappointed"]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = "positive"
            score = positive_count / (positive_count + negative_count + 1)
        elif negative_count > positive_count:
            sentiment = "negative"
            score = negative_count / (positive_count + negative_count + 1)
        else:
            sentiment = "neutral"
            score = 0.5
        
        return {
            "sentiment": sentiment,
            "score": score,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
    
    def _assess_complexity(self, text: str) -> Dict[str, Any]:
        """Assess the complexity of the input"""
        words = text.split()
        sentences = text.split('.')
        
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(sentences) if sentences else 0
        
        # Simple complexity score
        complexity_score = (avg_word_length * 0.3 + avg_sentence_length * 0.7) / 10
        complexity_score = min(complexity_score, 1.0)
        
        if complexity_score < 0.3:
            level = "simple"
        elif complexity_score < 0.7:
            level = "moderate"
        else:
            level = "complex"
        
        return {
            "level": level,
            "score": complexity_score,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_word_length": avg_word_length,
            "avg_sentence_length": avg_sentence_length
        }
    
    async def _detect_tool_needs(self, text: str) -> List[Dict[str, Any]]:
        """Detect if the input requires specific tools"""
        text_lower = text.lower()
        tool_requests = []
        
        for tool_name, patterns in self.tool_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Extract parameters based on tool type
                    parameters = await self._extract_tool_parameters(tool_name, text)
                    tool_requests.append({
                        "name": tool_name,
                        "parameters": parameters,
                        "confidence": 0.8  # Simple confidence score
                    })
                    break
        
        return tool_requests
    
    async def _extract_tool_parameters(self, tool_name: str, text: str) -> Dict[str, Any]:
        """Extract parameters for specific tools"""
        parameters = {}
        
        if tool_name == "web_search":
            # Extract search query
            search_patterns = [
                r"search for (.+)",
                r"google (.+)",
                r"find (.+)",
                r"look up (.+)"
            ]
            for pattern in search_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parameters["query"] = match.group(1).strip()
                    break
            if not parameters.get("query"):
                parameters["query"] = text  # Use full text as fallback
        
        elif tool_name == "calculator":
            # Extract mathematical expressions
            # First try to find explicit math expressions
            math_expressions = re.findall(r'\d+(?:\.\d+)?\s*[\+\-\*/\^]\s*\d+(?:\.\d+)?(?:\s*[\+\-\*/\^]\s*\d+(?:\.\d+)?)*', text)
            if math_expressions:
                parameters["expression"] = math_expressions[0]
            else:
                # Try to extract from "calculate X" pattern
                calc_match = re.search(r'calculate\s+(.+)', text, re.IGNORECASE)
                if calc_match:
                    parameters["expression"] = calc_match.group(1).strip()
                else:
                    # Look for any mathematical expression in the text
                    expr_match = re.search(r'(\d+(?:\.\d+)?\s*[\+\-\*/\^]\s*\d+(?:\.\d+)?(?:\s*[\+\-\*/\^]\s*\d+(?:\.\d+)?)*)', text)
                    if expr_match:
                        parameters["expression"] = expr_match.group(1).strip()
                    else:
                        parameters["expression"] = text
        
        elif tool_name == "code_executor":
            # Extract code blocks
            code_blocks = re.findall(r'```(?:python|javascript|js)?\n?(.*?)\n?```', text, re.DOTALL)
            if code_blocks:
                parameters["code"] = code_blocks[0]
                parameters["language"] = "python"  # Default
            else:
                parameters["code"] = text
                parameters["language"] = "python"
        
        elif tool_name == "file_manager":
            # Extract file operations
            if "save" in text.lower():
                parameters["operation"] = "save"
            elif "read" in text.lower() or "open" in text.lower():
                parameters["operation"] = "read"
            elif "create" in text.lower():
                parameters["operation"] = "create"
            else:
                parameters["operation"] = "read"
            
            # Extract file path
            file_paths = re.findall(r'[./]?[\w/.-]+\.\w+', text)
            if file_paths:
                parameters["file_path"] = file_paths[0]
        
        return parameters
    
    async def generate_response(self, messages: List[Message], context: Dict[str, Any], tool_calls: List[ToolCall] = None) -> str:
        """Generate a response based on messages and context"""
        if not self.client:
            await self.initialize()
        
        # If still no client (no API key), use fallback response
        if not self.client:
            return self._generate_fallback_response(messages, context, tool_calls)
        
        # Prepare conversation history for OpenAI
        openai_messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add recent conversation history
        for message in messages[-10:]:  # Last 10 messages
            openai_messages.append({
                "role": message.role,
                "content": message.content
            })
        
        # Add tool results if any
        if tool_calls:
            tool_results = []
            for tool_call in tool_calls:
                if tool_call.result:
                    tool_results.append(f"Tool '{tool_call.name}' result: {tool_call.result}")
                elif tool_call.error:
                    tool_results.append(f"Tool '{tool_call.name}' error: {tool_call.error}")
            
            if tool_results:
                openai_messages.append({
                    "role": "system",
                    "content": f"Tool execution results:\n" + "\n".join(tool_results)
                })
        
        # Add context information
        if context:
            context_info = []
            if context.get("intent"):
                context_info.append(f"User intent: {context['intent']['primary']}")
            if context.get("sentiment"):
                context_info.append(f"Sentiment: {context['sentiment']['sentiment']}")
            
            if context_info:
                openai_messages.append({
                    "role": "system",
                    "content": "Context: " + ", ".join(context_info)
                })
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
    
    def _generate_fallback_response(self, messages: List[Message], context: Dict[str, Any], tool_calls: List[ToolCall] = None) -> str:
        """Generate a fallback response when OpenAI is not available"""
        if not messages:
            return "Hello! I'm your AI assistant. How can I help you today?"
        
        last_message = messages[-1].content.lower()
        
        # Simple pattern matching for common queries
        if any(word in last_message for word in ["hello", "hi", "hey"]):
            return "Hello! I'm your AI assistant. How can I help you today?"
        elif any(word in last_message for word in ["how are you", "how do you do"]):
            return "I'm doing well, thank you! I'm here to help you with various tasks."
        elif "?" in last_message:
            return "That's an interesting question! I'd be happy to help, but I need an OpenAI API key to provide detailed responses. You can set it in your environment variables."
        elif tool_calls:
            tool_results = []
            for tool_call in tool_calls:
                if tool_call.result:
                    tool_results.append(f"I executed the {tool_call.name} tool and got: {tool_call.result}")
                elif tool_call.error:
                    tool_results.append(f"There was an error with the {tool_call.name} tool: {tool_call.error}")
            return "\n".join(tool_results) if tool_results else "I executed the requested tools."
        else:
            return "I understand you're trying to communicate with me. To provide better responses, please set up an OpenAI API key in your environment variables."
    
    async def summarize_conversation(self, messages: List[Message]) -> str:
        """Generate a summary of the conversation"""
        if not self.client or not messages:
            return "No conversation to summarize."
        
        # Prepare messages for summarization
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in messages
        ])
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Summarize the following conversation concisely:"},
                    {"role": "user", "content": conversation_text}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"