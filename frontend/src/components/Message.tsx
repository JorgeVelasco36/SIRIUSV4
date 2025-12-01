import React from 'react';
import './Message.css';
import ReactMarkdown from 'react-markdown';

interface MessageProps {
  text: string;
  isUser: boolean;
  timestamp: Date;
}

const Message: React.FC<MessageProps> = ({ text, isUser, timestamp }) => {
  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-content">
        <ReactMarkdown>{text}</ReactMarkdown>
      </div>
      <div className="message-timestamp">
        {timestamp.toLocaleTimeString('es-CO', { 
          hour: '2-digit', 
          minute: '2-digit' 
        })}
      </div>
    </div>
  );
};

export default Message;









