import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import fs from 'fs'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],

    server: {
        host: '0.0.0.0', // Listen on all network interfaces to expose the dev environment to smartphones on the local Wi-Fi
        port: 5173,
        allowedHosts: 'all',

        // Crate secure context (HTTPS) to unlock MediaDevices/getUserMedia camera permissions on mobile browsers
        https: {
            key: fs.readFileSync('../backend/localhost+3-key.pem'),
            cert: fs.readFileSync('../backend/localhost+3.pem')
        },

        // Reverse Proxy Engine to defeat Same-Origin Policy (SOP) blocks
        proxy: {
            '/registered': {
                target: 'http://127.0.0.1:5000', // Redirects frontend paths transparently to the Flask service
                changeOrigin: true,              // Modifies origin headers to match target expectations
                secure: false                    // Permits connection even if internal local transport lacks signed authorities
            }
        }
    }
})
