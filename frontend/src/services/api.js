import axios from 'axios';

const api = axios.create({
  baseURL: '/api', // Usando el proxy configurado en package.json
});

// Interceptor para añadir el token a las solicitudes
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      // Asegurarnos que el token tenga el formato correcto
      if (!token.startsWith('Bearer ')) {
        config.headers.Authorization = `Bearer ${token}`;
      } else {
        config.headers.Authorization = token;
      }
      
      // Debug para ver qué token se está enviando
      console.log('Sending request with token:', config.headers.Authorization);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Manejador global para respuestas 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      console.error('Authentication error:', error.response.data);
      
      // Solo limpiar el token si realmente es inválido
      // (no por otras razones como permisos insuficientes)
      if (error.response.data && error.response.data.detail === 'Invalid token') {
        console.log('Token inválido detectado, limpiando sesión...');
        localStorage.removeItem('token');
        // No redireccionar aquí para evitar ciclos
      }
    }
    
    // Asegurar que los errores de validación se manejen correctamente
    if (error.response?.data && typeof error.response.data === 'object') {
      // Si hay errores de validación, los mantenemos como están
      // para que los componentes puedan procesarlos correctamente
      console.log('Error response data:', error.response.data);
    }
    
    return Promise.reject(error);
  }
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
      // No necesitas añadir el token aquí, el interceptor lo hace
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
