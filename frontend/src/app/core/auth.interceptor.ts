import { HttpInterceptorFn } from '@angular/common/http';
import { API_BASE } from './api.config';

export const TOKEN_KEY = 'switchprep.token';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token && req.url.startsWith(`${API_BASE}/api/`)) {
    req = req.clone({ setHeaders: { Authorization: `Bearer ${token}` } });
  }
  return next(req);
};
