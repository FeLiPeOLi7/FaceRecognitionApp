import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

export function useSocket(serverUrl = '/') {
    const socketRef = useRef(null);
    const [processedSrc, setProcessedSrc] = useState('');
    const [socketError, setSocketError] = useState(false);

    useEffect(() => {
        socketRef.current = io(serverUrl, { autoConnect: true });

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
