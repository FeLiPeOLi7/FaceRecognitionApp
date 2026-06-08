import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import { getBackendUrl } from '../config/backendUrl';

export function useSocket(serverUrl = '/') {
    const socketRef = useRef(null); // Socket reference
    const [processedSrc, setProcessedSrc] = useState(''); // Ref to show processed img
    const [socketError, setSocketError] = useState(false); // Error status

    useEffect(() => {
        const resolvedServerUrl = serverUrl && serverUrl !== '/'
            ? serverUrl
            : getBackendUrl();

        // Starts socket connection with the server
        socketRef.current = io(resolvedServerUrl, {
            transports: ['websocket', 'polling'],
        });

        // Waits for the server to send the processed event
        socketRef.current.on('processed', (data) => {
            const blob = new Blob([data], { type: 'image/jpeg' });
            setProcessedSrc(URL.createObjectURL(blob));
        });

        socketRef.current.on('connect_error', (err) => {
            console.error('Socket.IO Error:', err);
            setSocketError(true);
        });

        return () => {
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, [serverUrl]);

    const emitFrame = (base64Data) => {
        if (socketRef.current && socketRef.current.connected) {
            socketRef.current.emit('frame', { image_b64: base64Data });
        }
    };

    return { emitFrame, processedSrc, socketError };
}
