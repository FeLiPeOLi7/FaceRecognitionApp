export function getBackendUrl() {
    const configuredUrl = import.meta.env.VITE_BACKEND_URL
        || import.meta.env.VITE_SOCKET_URL
        || import.meta.env.VITE_API_URL;

    if (configuredUrl) {
        return configuredUrl;
    }

    if (typeof window !== 'undefined' && window.location?.hostname) {
        return `${window.location.protocol}//${window.location.hostname}:5000`;
    }

    return 'http://localhost:5000';
}