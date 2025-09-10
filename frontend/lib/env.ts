// Environment configuration utilities for container and local development

export const ENV = {
  // API Configuration
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Session Configuration
  SESSION_ID: process.env.NEXT_PUBLIC_SESSION_ID || null,
  SESSION_TTL_HOURS: parseInt(process.env.NEXT_PUBLIC_SESSION_TTL_HOURS || '72'),
  
  // File Upload Configuration
  MAX_FILE_SIZE_MB: parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE_MB || '100'),
  ALLOWED_FILE_TYPES: (process.env.NEXT_PUBLIC_ALLOWED_FILE_TYPES || '.pdf,.txt,.docx').split(','),
  
  // Environment Detection
  IS_CONTAINERIZED: process.env.NEXT_PUBLIC_IS_CONTAINERIZED === 'true',
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
  IS_PRODUCTION: process.env.NODE_ENV === 'production',
} as const;

// Helper functions
export const getApiUrl = (endpoint: string = ''): string => {
  const baseUrl = ENV.API_URL.endsWith('/') ? ENV.API_URL.slice(0, -1) : ENV.API_URL;
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

export const isValidFileType = (filename: string): boolean => {
  const extension = filename.toLowerCase().substring(filename.lastIndexOf('.'));
  return ENV.ALLOWED_FILE_TYPES.includes(extension);
};

export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

export const getMaxFileSizeBytes = (): number => {
  return ENV.MAX_FILE_SIZE_MB * 1024 * 1024;
};