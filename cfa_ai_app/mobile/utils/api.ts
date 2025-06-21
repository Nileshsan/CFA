import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/', // Use your backend IP in production
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;


