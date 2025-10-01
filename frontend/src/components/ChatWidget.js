import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MessageCircle, X, Send, Loader, Sparkles } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const API = `${API_BASE}/api`;

const ChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [contextUsed, setContextUsed] = useState([]);
  const messagesEndRef = useRef(null);
  const token = localStorage.getItem('token');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          type: 'ai',
          content: "Hi! I'm your personal finance assistant. I can help you understand your spending, create budgets, and give you personalized financial advice. What would you like to know?",
          timestamp: new Date().toISOString()
        }
      ]);
    }
  }, [isOpen]);

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await axios.post(
        `${API}/chat/financial`,
        { message: inputMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.success) {
        setMessages(prev => [...prev, {
          type: 'ai',
          content: response.data.response,
          suggestions: response.data.suggestions,
          timestamp: new Date().toISOString()
        }]);
        setContextUsed(response.data.context_used || []);
      } else {
        setMessages(prev => [...prev, {
          type: 'ai',
          content: "I'm having trouble processing your request. Please try again.",
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setMessages(prev => [...prev, {
        type: 'ai',
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!token) return null;

  return (
    <>
      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 sm:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      <div className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-50">
        {/* Chat Button - Mobile Optimized */}
        {!isOpen && (
          <button
            onClick={() => setIsOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-green-600 text-white rounded-full p-3 sm:p-4 shadow-lg hover:shadow-xl transition-all transform hover:scale-110"
          >
            <MessageCircle className="w-5 h-5 sm:w-6 sm:h-6" />
          </button>
        )}

        {/* Chat Window - Mobile Full Screen */}
        {isOpen && (
          <div className="bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl fixed sm:relative inset-x-0 bottom-0 sm:inset-auto sm:w-96 h-[85vh] sm:h-[600px] flex flex-col overflow-hidden animate-in slide-in-from-bottom-5">
            {/* Header - Mobile Optimized */}
            <div className="bg-gradient-to-r from-blue-600 to-green-600 text-white p-3 sm:p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 sm:w-5 sm:h-5" />
                <div>
                  <h3 className="font-bold text-sm sm:text-base">AI Assistant</h3>
                  {contextUsed.length > 0 && (
                    <p className="text-[10px] sm:text-xs opacity-90 hidden sm:block">
                      Using: {contextUsed.join(', ')}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="hover:bg-white/20 rounded-lg p-1 transition-colors"
              >
                <X className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
            </div>

            {/* Messages - Mobile Optimized */}
            <div className="flex-1 overflow-y-auto p-3 sm:p-4 space-y-3 sm:space-y-4 bg-gray-50">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] sm:max-w-[80%] rounded-2xl p-2 sm:p-3 ${
                    msg.type === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-800 shadow-sm'
                  }`}
                >
                  <p className="text-xs sm:text-sm whitespace-pre-line">{msg.content}</p>
                  {msg.suggestions && (
                    <div className="mt-2 space-y-1">
                      {msg.suggestions.map((suggestion, i) => (
                        <button
                          key={i}
                          onClick={() => setInputMessage(suggestion)}
                          className="block w-full text-left text-[10px] sm:text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded hover:bg-blue-100 transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white rounded-2xl p-2 sm:p-3 shadow-sm">
                  <Loader className="w-4 h-4 sm:w-5 sm:h-5 animate-spin text-blue-600" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input - Mobile Optimized */}
          <div className="p-3 sm:p-4 bg-white border-t border-gray-200">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about your finances..."
                className="flex-1 px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 rounded-xl focus:outline-none focus:border-blue-600"
                disabled={loading}
              />
              <button
                onClick={sendMessage}
                disabled={loading || !inputMessage.trim()}
                className="bg-blue-600 text-white p-2 rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              >
                <Send className="w-4 h-4 sm:w-5 sm:h-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </>
  );
};

export default ChatWidget;
