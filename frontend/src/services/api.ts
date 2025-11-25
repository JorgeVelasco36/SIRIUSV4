import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface ChatResponse {
  answer: string;
  data?: any;
  recommendations?: string[];
  metadata?: any;
}

export interface ChatMessage {
  message: string;
  user?: string;
  filters?: any;
}

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const sendMessage = async (message: string, user?: string): Promise<ChatResponse> => {
  const response = await api.post('/api/v1/chat', {
    message,
    user,
  });
  return response.data;
};

export const getValuations = async (params: any) => {
  const response = await api.get('/api/v1/valuations', { params });
  return response.data;
};

export const compareProviders = async (isin: string, fecha?: string) => {
  const params = fecha ? { fecha } : {};
  const response = await api.get(`/api/v1/valuations/compare?isin=${isin}`, { params });
  return response.data;
};

export const getAlerts = async (isin: string, fecha?: string) => {
  const params = fecha ? { fecha } : {};
  const response = await api.get(`/api/v1/valuations/${isin}/alerts`, { params });
  return response.data;
};

export const uploadFile = async (file: File, provider: string, fecha?: string) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('provider', provider);
  if (fecha) {
    formData.append('fecha_valoracion', fecha);
  }
  const response = await api.post('/api/v1/ingest/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getStats = async () => {
  const response = await api.get('/api/v1/stats');
  return response.data;
};

export default api;






