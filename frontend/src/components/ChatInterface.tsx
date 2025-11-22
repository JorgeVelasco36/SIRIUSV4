import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import MessageList from './MessageList';
import MessageInput from './MessageInput';
import FiltersPanel from './FiltersPanel';
import { sendMessage, ChatResponse } from '../services/api';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  data?: any;
  recommendations?: string[];
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState({
    fecha: '',
    proveedor: '',
    isins: ''
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    // Agregar mensaje del usuario
    const userMessage: Message = {
      id: Date.now().toString(),
      text,
      isUser: true,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Construir mensaje con filtros si aplican
      let messageText = text;
      if (filters.fecha) {
        messageText += ` (fecha: ${filters.fecha})`;
      }
      if (filters.proveedor) {
        messageText += ` (proveedor: ${filters.proveedor})`;
      }
      if (filters.isins) {
        messageText += ` (ISINs: ${filters.isins})`;
      }

      const response: ChatResponse = await sendMessage(messageText);
      
      // Agregar respuesta del asistente
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.answer,
        isUser: false,
        timestamp: new Date(),
        data: response.data,
        recommendations: response.recommendations
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: 'Error al procesar la consulta. Por favor, intenta nuevamente.',
        isUser: false,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  return (
    <div className="chat-interface">
      <FiltersPanel
        filters={filters}
        onFiltersChange={setFilters}
      />
      <div className="chat-main">
        <MessageList
          messages={messages}
          isLoading={isLoading}
        />
        <div ref={messagesEndRef} />
        <MessageInput
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};

export default ChatInterface;



