import React from 'react';
import './MessageList.css';
import Message from './Message';
import ValuationTable from './ValuationTable';

interface MessageProps {
  messages: Array<{
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
    data?: any;
    recommendations?: string[];
  }>;
  isLoading: boolean;
}

const MessageList: React.FC<MessageProps> = ({ messages, isLoading }) => {
  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="welcome-message">
          <h2>Bienvenido a S.I.R.I.U.S V4</h2>
          <p>Puedes hacer consultas como:</p>
          <ul>
            <li>"¿Cuál es el precio limpio del TES CO000123 hoy en Precia?"</li>
            <li>"Compara PIP Latam vs Precia para este ISIN."</li>
            <li>"Trae valoración de ayer para estos 5 ISINs."</li>
          </ul>
        </div>
      )}
      
      {messages.map(message => (
        <div key={message.id}>
          <Message
            text={message.text}
            isUser={message.isUser}
            timestamp={message.timestamp}
          />
          {message.data && !message.isUser && (
            <div className="message-data">
              {Array.isArray(message.data) ? (
                <ValuationTable data={message.data} />
              ) : (
                <ValuationTable data={[message.data]} />
              )}
            </div>
          )}
          {message.recommendations && message.recommendations.length > 0 && (
            <div className="recommendations">
              <h4>Recomendaciones:</h4>
              <ul>
                {message.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ))}
      
      {isLoading && (
        <div className="loading-message">
          <div className="loading-spinner"></div>
          <span>Procesando consulta...</span>
        </div>
      )}
    </div>
  );
};

export default MessageList;








