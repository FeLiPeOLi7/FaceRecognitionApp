export const getBackendUrl = () => {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        return '';
    }
    return 'http://127.0.0.1:5000';
};
