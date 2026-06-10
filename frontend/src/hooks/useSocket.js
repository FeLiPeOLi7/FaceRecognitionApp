import { useEffect, useRef, useState } from 'react';
import { getBackendUrl } from '../config/backendUrl';

export function useSocket(serverUrl = '/') {
    const [processedSrc, setProcessedSrc] = useState(''); // Ref to show processed img
    const [socketError, setSocketError] = useState(false); // Error status
    const backendUrlRef = useRef('');
    const isProcessingRef = useRef(false); // Controle para evitar requisicoes paralelas

    useEffect(() => {
        const resolvedServerUrl = serverUrl && serverUrl !== '/'
            ? serverUrl
            : getBackendUrl();
        
        backendUrlRef.current = resolvedServerUrl;
    }, [serverUrl]);

    const clientId = crypto.randomUUID();

    const emitFrame = async (base64Data) => {
        // Evitar multiplas requisicoes paralelas
        if (isProcessingRef.current) {
            return;
        }

        isProcessingRef.current = true;

        try {
            const backendUrl = backendUrlRef.current;
            const response = await fetch(`${backendUrl}/frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    //client_id: clientId,
                    image_b64: base64Data,
                }),
            });

            if (!response.ok) {
                console.error(`Server error: ${response.status}`);
                setSocketError(true);
                return;
            }

            // Ler resposta como blob (JPEG)
            const blob = await response.blob();
            setProcessedSrc(URL.createObjectURL(blob));
            setSocketError(false);
        } catch (error) {
            console.error('Fetch error:', error);
            setSocketError(true);
        } finally {
            isProcessingRef.current = false;
        }
    };

    return { emitFrame, processedSrc, socketError };
}