import { createApp } from 'vue'
import './styles/main.css'
import App from './App.vue'

// Initialize theme from localStorage before app mounts to prevent flash
const savedTheme = localStorage.getItem('theme') as 'light' | 'dark' | null;
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light');
document.documentElement.classList.add(initialTheme);

createApp(App).mount('#app')
