/**
 * buildOS Dashboard Configuration
 */

const SERVER_PORT = import.meta.env.VITE_API_PORT || '4000';

// In production, use same origin (empty string means relative URLs)
// In development, use localhost with port
const isProduction = import.meta.env.PROD;
const defaultApiUrl = isProduction ? '' : `http://localhost:${SERVER_PORT}`;
const defaultWsUrl = isProduction 
  ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/stream`
  : `ws://localhost:${SERVER_PORT}/stream`;

export const API_BASE_URL = import.meta.env.VITE_API_URL || defaultApiUrl;
export const WS_URL = import.meta.env.VITE_WS_URL || defaultWsUrl;
export const MAX_EVENTS = parseInt(import.meta.env.VITE_MAX_EVENTS || '300');
