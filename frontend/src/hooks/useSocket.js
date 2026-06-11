import { useEffect, useRef, useState } from 'react';
import { getSocketBackendUrl } from '../config/backendUrl';

export function useSocket(serverUrl = '/') {
    const [processedSrc, setProcessedSrc] = useState(''); // Store local Blob URL of processed frame response
    const [socketError, setSocketError] = useState(false); // Track network connection/processing drops
    const backendUrlRef = useRef(''); // Ref for the Backend URL
    const isProcessingRef = useRef(false); // Network throttle lock to block simultaneous HTTP polling pile-ups

    // Resolve socket server destination string on parameter change
    useEffect(() => {
        const resolvedServerUrl = serverUrl && serverUrl !== '/'
            ? serverUrl
            : getSocketBackendUrl();
        backendUrlRef.current = resolvedServerUrl;
    }, [serverUrl]);

    // Instantiate an immutable unique identifier for server-side face tracking cache isolation
    const clientId = crypto.randomUUID();

    // Serializes base64 image data into JSON and issues HTTP polling request to raw socket port 5001
    const emitFrame = async (base64Data) => {
        // Drop tick if the previous network packet has not completed its round-trip loop
        if (isProcessingRef.current) {
            return;
        }

        isProcessingRef.current = true; // Engage throttle lock

        try {
            // HTTP POST
            const backendUrl = backendUrlRef.current;
            const response = await fetch(`${backendUrl}/frame`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    client_id: clientId,
                    image_b64: base64Data,
                }),
            });

            if (!response.ok) {
                console.error(`Server error: ${response.status}`);
                setSocketError(true);
                return;
            }

            // Read response stream as pure binary data
            const blob = await response.blob();

            // Map the binary image layout directly into an ephemeral local memory reference URL
            setProcessedSrc(URL.createObjectURL(blob));
            setSocketError(false);
        } catch (error) {
            console.error('Fetch error:', error);
            setSocketError(true);
        } finally {
            isProcessingRef.current = false; // Disengage lock, allowing next frame dispatch
        }
    };
    return { emitFrame, processedSrc, socketError };
}
