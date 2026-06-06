import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
}

interface Session {
  session_id: string;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('Connecting...');
  const [models, setModels] = useState<string[]>(['qwen2.5:0.5b']);
  const [selectedModel, setSelectedModel] = useState('qwen2.5:0.5b');
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const chatBoxRef = useRef<HTMLDivElement>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    checkBackendConnection();
    loadSessions();
  }, []);

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [messages]);

  const checkBackendConnection = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/health`, { timeout: 5000 });
      setStatus(`✅ Connected • ${response.data.models || 0} model(s) ready`);
      
      try {
        const modelsResponse = await axios.get(`${API_URL}/api/models`);
        setModels(modelsResponse.data.models || ['qwen2.5:0.5b']);
        setSelectedModel(modelsResponse.data.default || 'qwen2.5:0.5b');
      } catch (e) {
        console.error('Error fetching models:', e);
      }
    } catch (error) {
      setStatus('❌ Cannot connect to backend');
    }
  };

  const loadSessions = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/sessions`);
      setSessions(response.data.sessions || []);
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await axios.post(`${API_URL}/api/sessions?title=New Chat`);
      setCurrentSession(response.data.session_id);
      setMessages([]);
      loadSessions();
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const loadSession = async (sessionId: string) => {
    try {
      const response = await axios.get(`${API_URL}/api/sessions/${sessionId}`);
      const loadedMessages = response.data.messages.map((msg: any, idx: number) => ({
        id: idx.toString(),
        text: msg.content,
        sender: msg.role === 'user' ? 'user' : 'assistant',
        timestamp: new Date(msg.timestamp)
      }));
      setMessages(loadedMessages);
      setCurrentSession(sessionId);
    } catch (error) {
      console.error('Error loading session:', error);
    }
  };

  const clearHistory = () => {
    setMessages([]);
    if (currentSession) {
      setCurrentSession(null);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await axios.delete(`${API_URL}/api/sessions/${sessionId}`);
      loadSessions();
      if (currentSession === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    if (!currentSession) {
      const response = await axios.post(`${API_URL}/api/sessions?title=New Chat`);
      setCurrentSession(response.data.session_id);
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages([...messages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/chat`, {
        message: input,
        history: messages.map(m => ({ role: m.sender === 'user' ? 'user' : 'assistant', content: m.text })),
        model: selectedModel,
        session_id: currentSession
      });

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.data.response || 'No response',
        sender: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      loadSessions();
    } catch (error: any) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Error: ${error.response?.data?.detail || error.message}`,
        sender: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app-container">
      <div className="app">
        <div className="header">
          <h1>💬 Qwen Chat</h1>
          <p>{status}</p>
        </div>

        <div className="model-selector-container">
          <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
            {models.map(model => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
          <div className="history-buttons">
            <button onClick={createNewSession}>📝 New</button>
            <button onClick={clearHistory}>🗑️ Clear</button>
          </div>
        </div>

        <div className="chat-box" ref={chatBoxRef}>
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome to Qwen Chat</h2>
              <p>Select a model and start a conversation.</p>
              {sessions.length > 0 && (
                <div style={{ marginTop: '20px', width: '100%' }}>
                  <h3 style={{ color: '#0099FF', marginBottom: '10px' }}>Recent Chats</h3>
                  {sessions.slice(0, 5).map(session => (
                    <div key={session.session_id} style={{ 
                      display: 'flex', 
                      gap: '8px', 
                      marginBottom: '8px',
                      padding: '8px',
                      background: '#E0F2FF',
                      borderRadius: '6px',
                      alignItems: 'center'
                    }}>
                      <button 
                        onClick={() => loadSession(session.session_id)}
                        style={{ flex: 1, textAlign: 'left', padding: '6px 12px', fontSize: '12px' }}
                      >
                        {session.title}
                      </button>
                      <button 
                        onClick={() => deleteSession(session.session_id)}
                        style={{ padding: '4px 8px', fontSize: '11px' }}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`message message-${msg.sender}`}>
              <div className="message-content">
                {msg.text}
              </div>
              <span className="message-time">
                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          ))}

          {loading && (
            <div className="message message-assistant">
              <div className="message-content">
                <div className="typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="input-area">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message... (Shift+Enter for new line)"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
