import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],

    server: {
        host: '0.0.0.0',
        port: 5173,
        allowedHosts: 'all',
        https: {
            key: fs.readFileSync('../backend/localhost+3-key.pem'), 
            cert: fs.readFileSync('../backend/localhost+3.pem')
        },
        proxy: {
            '/registered': {
                target: 'http://127.0.0.1:5000',
                changeOrigin: true,
                secure: false
            },
            '/socket.io': {
                target: 'http://127.0.0.1:5000',
                ws: true,
                changeOrigin: true,
                secure: false
            }
        }
    }
})
