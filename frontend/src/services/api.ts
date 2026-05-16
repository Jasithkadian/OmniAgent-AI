import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const workflowService = {
  run: async (objective: string, document_ids: string[] = []) => {
    const response = await api.post('/workflows/run', { objective, document_ids });
    return response.data;
  },
};

export const documentService = {
  upload: async (file: File, conversation_id?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (conversation_id) {
      formData.append('conversation_id', conversation_id);
    }
    const response = await api.post('/documents/ingest', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  search: async (query: string, document_ids?: string[]) => {
    const response = await api.post('/documents/search', { query, document_ids });
    return response.data;
  },
};

export const healthService = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;
