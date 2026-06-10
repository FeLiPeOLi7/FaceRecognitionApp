export function getSocketBackendUrl() {
    const configuredUrl = import.meta.env.VITE_BACKEND_URL
        || import.meta.env.VITE_SOCKET_URL
        || import.meta.env.VITE_API_URL;

    if (configuredUrl) {
        return configuredUrl;
    }

    if (typeof window !== 'undefined' && window.location?.hostname) {
        console.log(`http://${window.location.hostname}:5001`)
        return `http://${window.location.hostname}:5001`;
    }

    return 'http://localhost:5001';
}

export const getFlaskBackendUrl = () => {
    if(window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return '';
    }
    return 'http://127.0.0.1:5000';
};
