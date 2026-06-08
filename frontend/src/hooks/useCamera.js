import { useRef, useState } from 'react';

export function useCamera(fps = 5) {
    const [capturing, setCapturing] = useState(false); // Is capturing state
    const [status, setStatus] = useState('Pronto'); // Camera state

    const streamRef = useRef(null); // Data stream
    const timerIdRef = useRef(null); // Timer for FPS ticks
    const frameInFlightRef = useRef(false); // Is sending data

    const videoElementRef = useRef(null); // Video reference
    const canvasElementRef = useRef(null); // Canvas reference

    const intervalMs = Math.max(1000 / fps, 120); // Time interval for ticks

    const stopCapture = () => {
        if (timerIdRef.current)
            clearInterval(timerIdRef.current);

        timerIdRef.current = null;
        frameInFlightRef.current = false;

        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }

        setCapturing(false);
        setStatus('Parado');
    };

    const startCapture = async (onFrameCallback) => {
        if (streamRef.current) return;

        setStatus('Iniciando câmera...');
        try {
            // Requests and setup Camera
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720, facingMode: 'user' },
                audio: false,
            });

            streamRef.current = stream;

            if (videoElementRef.current) {
                videoElementRef.current.srcObject = stream;
            }

            if (canvasElementRef.current) {
                canvasElementRef.current.width = 1280;
                canvasElementRef.current.height = 720;
            }

            setCapturing(true);
            setStatus(`Capturando a ${fps} FPS`);

            const ctx = canvasElementRef.current.getContext('2d');

            // Draw image on the canvas and saves the image
            timerIdRef.current = setInterval(() => {
                if (!streamRef.current || frameInFlightRef.current || !videoElementRef.current || videoElementRef.current.readyState < 2) return;

                // Drawing
                frameInFlightRef.current = true;
                ctx.drawImage(videoElementRef.current, 0, 0, 1280, 720);

                // Saving
                // Signature: canvas.toBlob(callback, type, quality)
                canvasElementRef.current.toBlob((blob) => {
                    if (!blob) {
                        frameInFlightRef.current = false;
                        return;
                    }

                    const reader = new FileReader();
                    reader.onloadend = () => {
                        // Removing image prefix
                        const result = String(reader.result || '');
                        const base64 = result.includes(',') ? result.split(',')[1] : '';
                        // Send image to socket
                        onFrameCallback(base64);
                        frameInFlightRef.current = false;
                    };
                    reader.readAsDataURL(blob);
                }, 'image/jpeg', 0.85); // Pa
            }, intervalMs);

        } catch (err) {
            console.error(err);
            setStatus('Erro ao acessar webcam');
            stopCapture();
        }
    };

    return {
        capturing,
        status,
        setStatus,
        startCapture,
        stopCapture,
        videoElementRef,
        canvasElementRef
    };
}
