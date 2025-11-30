# AI Agent System

A comprehensive, fully-functional AI agent system with tool integration, memory management, and web interface capabilities.

## Features

### 🤖 Core AI Agent
- **Intelligent Conversation**: Natural language processing with OpenAI integration
- **Context Awareness**: Maintains conversation context and memory across sessions
- **Intent Recognition**: Understands user intents and responds appropriately
- **Entity Extraction**: Identifies and extracts relevant entities from user input

### 🛠️ Tool Integration
- **Calculator**: Perform mathematical calculations and solve equations
- **Web Search**: Search the web for information (simulated implementation)
- **Code Executor**: Execute Python, JavaScript, and Bash code safely
- **File Manager**: Read, write, and manage files with security restrictions
- **Extensible Architecture**: Easy to add new tools and capabilities

### 🧠 Memory Management
- **Persistent Storage**: SQLite-based conversation history storage
- **Semantic Search**: Find relevant past conversations using similarity matching
- **Context Management**: Intelligent context window management for optimal performance
- **Multi-User Support**: Separate conversation histories for different users

### 🌐 Web Interface
- **Modern Chat UI**: Beautiful, responsive chat interface
- **Real-time Communication**: WebSocket support for instant messaging
- **REST API**: Comprehensive API for programmatic access
- **Tool Visualization**: Display tool usage and results in the chat

### ⚙️ Configuration & Customization
- **Environment-based Config**: Easy configuration through environment variables
- **Flexible Settings**: Customize agent behavior, tools, and appearance
- **Logging**: Comprehensive logging with configurable levels
- **Security**: Built-in security measures and input validation

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key (optional, for full NLP features)

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ai-agent-system
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Run the application**:
```bash
python main.py
```

5. **Open your browser** and navigate to `http://localhost:12000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI Configuration (optional)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Agent Configuration
AGENT_NAME=AI Assistant
AGENT_DESCRIPTION=A helpful AI assistant with tool integration
MAX_CONTEXT_TOKENS=4000

# Database
DATABASE_URL=sqlite:///ai_agent.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=ai_agent.log

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Customizing Tools

Add new tools by creating a class that inherits from `BaseTool`:

```python
from ai_agent.core.base import BaseTool

class MyCustomTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="my_tool",
            description="Description of what this tool does"
        )
    
    async def execute(self, parameters):
        # Tool implementation
        return {"result": "Tool output"}
    
    def get_schema(self):
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter description"}
            },
            "required": ["param1"]
        }
```

## API Documentation

### REST Endpoints

#### Chat
- **POST** `/chat` - Send a message to the agent
- **GET** `/agent/history` - Get conversation history
- **GET** `/agent/search` - Search conversation history

#### Agent Management
- **GET** `/agent/stats` - Get agent statistics
- **GET** `/agent/tools` - Get available tools
- **POST** `/agent/reset` - Reset agent session

#### WebSocket
- **WS** `/ws/chat` - Real-time chat communication

### Example API Usage

```python
import requests

# Send a message
response = requests.post("http://localhost:12000/chat", json={
    "message": "Calculate 2 + 2",
    "user_id": "user123"
})

print(response.json())
# Output: {"response": "The result is 4", "tool_calls": [...]}
```

## Architecture

### System Components

```
ai_agent/
├── core/           # Core agent framework
│   ├── base.py     # Abstract base classes
│   ├── agent.py    # Main AI agent implementation
│   └── models.py   # Data models
├── nlp/            # Natural language processing
│   └── processor.py # NLP processor with OpenAI integration
├── tools/          # Tool implementations
│   ├── calculator.py
│   ├── web_search.py
│   ├── code_executor.py
│   ├── file_manager.py
│   └── tool_manager.py
├── memory/         # Memory management
│   └── memory_manager.py
├── api/            # REST API
│   └── routes.py
├── web/            # Web interface
│   ├── static/     # CSS, JS files
│   └── templates/  # HTML templates
├── config/         # Configuration
│   └── settings.py
└── utils/          # Utilities
    ├── logger.py
    └── text_similarity.py
```

### Data Flow

1. **User Input** → Web Interface or API
2. **Message Processing** → NLP Processor
3. **Intent Recognition** → Agent Core
4. **Tool Selection** → Tool Manager
5. **Tool Execution** → Specific Tools
6. **Response Generation** → NLP Processor
7. **Memory Storage** → Memory Manager
8. **Response Delivery** → User Interface

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tools.py

# Run with coverage
pytest --cov=ai_agent

# Run integration tests
pytest -m integration
```

### Test Coverage

- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **API Tests**: REST API endpoint testing
- **Memory Tests**: Database and search functionality

## Development

### Adding New Features

1. **Create Feature Branch**:
```bash
git checkout -b feature/new-feature
```

2. **Implement Feature**:
   - Add code in appropriate module
   - Write tests
   - Update documentation

3. **Test Implementation**:
```bash
pytest tests/
```

4. **Submit Pull Request**

### Code Style

- Follow PEP 8 guidelines
- Use type hints
- Write comprehensive docstrings
- Maintain test coverage above 80%

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 12000

CMD ["python", "main.py"]
```

### Production Considerations

- Use a production WSGI server (e.g., Gunicorn)
- Set up proper logging and monitoring
- Configure environment variables securely
- Use a production database (PostgreSQL recommended)
- Set up SSL/TLS certificates
- Implement rate limiting and authentication

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**:
   - Check API key validity
   - Verify rate limits
   - Check network connectivity

2. **Database Issues**:
   - Ensure write permissions
   - Check disk space
   - Verify database file path

3. **Tool Execution Failures**:
   - Check tool permissions
   - Verify required dependencies
   - Review security restrictions

### Logging

Check logs for detailed error information:

```bash
tail -f ai_agent.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review existing issues and discussions

## Roadmap

### Upcoming Features
- [ ] Advanced tool chaining
- [ ] Plugin system for external tools
- [ ] Multi-modal support (images, audio)
- [ ] Advanced analytics and insights
- [ ] Team collaboration features
- [ ] Mobile app interface

### Performance Improvements
- [ ] Caching layer implementation
- [ ] Database query optimization
- [ ] Async processing enhancements
- [ ] Memory usage optimization