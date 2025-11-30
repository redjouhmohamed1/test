// AI Agent Chat Interface JavaScript

class ChatInterface {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.statusIndicator = document.querySelector('.status-indicator');
        
        this.websocket = null;
        this.isConnected = false;
        
        this.initializeEventListeners();
        this.connectWebSocket();
    }
    
    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Enter key press
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Control buttons
        document.getElementById('clearChat').addEventListener('click', () => this.clearChat());
        document.getElementById('resetAgent').addEventListener('click', () => this.resetAgent());
        document.getElementById('showStats').addEventListener('click', () => this.showStats());
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/chat`;
        
        try {
            this.websocket = new WebSocket(wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.updateConnectionStatus(true);
            };
            
            this.websocket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleResponse(data);
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect after 3 seconds
                setTimeout(() => this.connectWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.showError('Connection error. Please refresh the page.');
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.fallbackToHTTP();
        }
    }
    
    fallbackToHTTP() {
        console.log('Falling back to HTTP API');
        this.isConnected = true; // Set to true for HTTP fallback
        this.updateConnectionStatus(true);
    }
    
    updateConnectionStatus(connected) {
        if (connected) {
            this.statusIndicator.style.background = '#4CAF50';
            this.statusIndicator.title = 'Connected';
        } else {
            this.statusIndicator.style.background = '#f44336';
            this.statusIndicator.title = 'Disconnected';
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.addMessage('user', message);
        this.messageInput.value = '';
        this.showTyping(true);
        this.setSendButtonState(false);
        
        try {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                // Send via WebSocket
                this.websocket.send(JSON.stringify({
                    message: message,
                    user_id: this.getUserId()
                }));
            } else {
                // Fallback to HTTP API
                await this.sendMessageHTTP(message);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
            this.showTyping(false);
            this.setSendButtonState(true);
        }
    }
    
    async sendMessageHTTP(message) {
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: this.getUserId()
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.handleResponse(data);
            
        } catch (error) {
            console.error('HTTP request failed:', error);
            this.showError('Failed to send message. Please try again.');
        }
    }
    
    handleResponse(data) {
        this.showTyping(false);
        this.setSendButtonState(true);
        
        if (data.error) {
            this.showError(data.error);
            return;
        }
        
        // Add assistant response
        this.addMessage('assistant', data.response, data.tool_calls);
        
        // Scroll to bottom
        this.scrollToBottom();
    }
    
    addMessage(role, content, toolCalls = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? 'U' : 'AI';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const contentDiv = document.createElement('div');
        contentDiv.textContent = content;
        messageContent.appendChild(contentDiv);
        
        // Add tool calls if present
        if (toolCalls && toolCalls.length > 0) {
            const toolCallsDiv = document.createElement('div');
            toolCallsDiv.className = 'tool-calls';
            toolCallsDiv.innerHTML = '<strong>Tools used:</strong>';
            
            toolCalls.forEach(toolCall => {
                const toolDiv = document.createElement('div');
                toolDiv.className = 'tool-call';
                toolDiv.textContent = `${toolCall.tool_name}: ${JSON.stringify(toolCall.parameters)}`;
                toolCallsDiv.appendChild(toolDiv);
            });
            
            messageContent.appendChild(toolCallsDiv);
        }
        
        const timeDiv = document.createElement('div');
        timeDiv.className = 'message-time';
        timeDiv.textContent = new Date().toLocaleTimeString();
        messageContent.appendChild(timeDiv);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTyping(show) {
        if (show) {
            this.typingIndicator.classList.add('show');
        } else {
            this.typingIndicator.classList.remove('show');
        }
    }
    
    setSendButtonState(enabled) {
        this.sendButton.disabled = !enabled;
        this.sendButton.textContent = enabled ? 'Send' : 'Sending...';
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = `Error: ${message}`;
        
        this.messagesContainer.appendChild(errorDiv);
        this.scrollToBottom();
        
        // Remove error message after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    clearChat() {
        this.messagesContainer.innerHTML = '';
    }
    
    async resetAgent() {
        try {
            const response = await fetch('/agent/reset', {
                method: 'POST'
            });
            
            if (response.ok) {
                this.clearChat();
                this.addMessage('assistant', 'Agent session has been reset. How can I help you?');
            } else {
                this.showError('Failed to reset agent');
            }
        } catch (error) {
            console.error('Error resetting agent:', error);
            this.showError('Failed to reset agent');
        }
    }
    
    async showStats() {
        try {
            const response = await fetch('/agent/stats');
            
            if (response.ok) {
                const stats = await response.json();
                const statsMessage = `Agent Statistics:
• Name: ${stats.name}
• Session ID: ${stats.session_id}
• Messages: ${stats.message_count}
• Available Tools: ${stats.available_tools.join(', ')}
• Context Size: ${stats.conversation_context_size}
• Uptime: ${stats.uptime.toFixed(2)}s`;
                
                this.addMessage('assistant', statsMessage);
            } else {
                this.showError('Failed to get agent stats');
            }
        } catch (error) {
            console.error('Error getting stats:', error);
            this.showError('Failed to get agent stats');
        }
    }
    
    getUserId() {
        // Simple user ID generation/storage
        let userId = localStorage.getItem('ai_agent_user_id');
        if (!userId) {
            userId = 'user_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('ai_agent_user_id', userId);
        }
        return userId;
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});