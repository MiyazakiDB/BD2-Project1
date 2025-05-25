import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // Usando el proxy configurado en package.json
});

// Interceptor para añadir el token a las solicitudes
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Servicios de autenticación
export const authService = {
  register: (userData) => api.post('/auth/register', userData),
  login: (userData) => api.post('/auth/login', userData),
};

// Servicios de gestión de archivos
export const fileService = {
  uploadFile: (formData) => api.post('/files/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  listFiles: () => api.get('/files'),
  deleteFile: (filename) => api.delete(`/files/${filename}`),
};

// Servicios de gestión de tablas
export const tableService = {
  createTable: (tableData) => api.post('/tables/create', tableData),
  listTables: () => api.get('/tables'),
  deleteTable: (tableName) => api.delete(`/tables/${tableName}`),
  getTableData: (tableName, page = 1) => api.get(`/tables/${tableName}/data?page=${page}`),
};

// Servicio de consultas
export const queryService = {
  executeQuery: (query) => api.post('/query', { query }),
};

// Servicio de métricas
export const metricsService = {
  getMetrics: () => api.get('/metrics'),
};

export default api;
