import React, { useState, useEffect, useRef } from 'react';
import { chatAPI } from '../api';

function Chat({ onLogout }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage = { role: 'user', content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await chatAPI.sendMessage(input, sessionId);

            // Store session ID for future messages
            if (response.session_id) {
                setSessionId(response.session_id);
            }

            const botMessage = {
                role: 'assistant',
                content: response.response
            };
            setMessages((prev) => [...prev, botMessage]);
        } catch (error) {
            const errorMessage = {
                role: 'assistant',
                content: 'Sorry, there was an error processing your request.'
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="chat-container">
            <header className="chat-header">
                <h1>SIHRA - HR Assistant</h1>
                <button onClick={onLogout} className="btn-logout">Logout</button>
            </header>

            <div className="messages-container">
                {messages.length === 0 && (
                    <div className="welcome-message">
                        <h2>Welcome to SIHRA!</h2>
                        <p>Ask me anything about HR policies, holidays, leave, or work from home.</p>
                    </div>
                )}

                {messages.map((msg, idx) => (
                    <div key={idx} className={`message message-${msg.role}`}>
                        <div className="message-avatar">
                            {msg.role === 'user' ? '👤' : '🤖'}
                        </div>
                        <div className="message-content">
                            <pre>{msg.content}</pre>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="message message-assistant">
                        <div className="message-avatar">🤖</div>
                        <div className="message-content">
                            <div className="typing-indicator">
                                <span></span><span></span><span></span>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="input-container">
                <textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about holidays, policies, leave..."
                    disabled={loading}
                    rows="2"
                />
                <button
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                    className="btn-send"
                >
                    Send
                </button>
            </div>
        </div>
    );
}

export default Chat;
