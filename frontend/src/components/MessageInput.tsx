import React, { useState, KeyboardEvent } from 'react';
import './MessageInput.css';

interface MessageInputProps {
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

const MessageInput: React.FC<MessageInputProps> = ({ onSendMessage, isLoading }) => {
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="message-input">
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder="Escribe tu consulta aquí... (Enter para enviar, Shift+Enter para nueva línea)"
        rows={2}
        disabled={isLoading}
      />
      <button
        onClick={handleSend}
        disabled={!input.trim() || isLoading}
        className="send-button"
      >
        Enviar
      </button>
    </div>
  );
};

export default MessageInput;









