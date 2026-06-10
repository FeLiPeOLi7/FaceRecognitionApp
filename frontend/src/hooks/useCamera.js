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
            const isMobilePortrait = window.innerHeight > window.innerWidth;
            const constraints = {
                video: {
                    width: isMobilePortrait ? { ideal: 720 } : { ideal: 1280 },
                    height: isMobilePortrait ? { ideal: 1280 } : { ideal: 720 },
                    facingMode: 'user',
                },
                audio: false,
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            streamRef.current = stream;

            if (videoElementRef.current) {
                videoElementRef.current.srcObject = stream;
            }

            await new Promise((resolve) => {
                if (videoElementRef.current) {
                    videoElementRef.current.onloadedmetadata = () => resolve();
                } else {
                    resolve();
                }
            });

            const videoTrack = stream.getVideoTracks()[0];
            const { width: realWidth, height: realHeight } = videoTrack.getSettings();

            if (canvasElementRef.current) {
                canvasElementRef.current.width = realWidth;
                canvasElementRef.current.height = realHeight;
            }

            setCapturing(true);
            setStatus(`Capturando video`);

            const ctx = canvasElementRef.current.getContext('2d');

            timerIdRef.current = setInterval(() => {
                if (
                    !streamRef.current || 
                        frameInFlightRef.current || 
                        !videoElementRef.current || 
                        videoElementRef.current.readyState < 2
                ) return;

                frameInFlightRef.current = true;

                ctx.drawImage(videoElementRef.current, 0, 0, realWidth, realHeight);

                canvasElementRef.current.toBlob((blob) => {
                    if (!blob) {
                        frameInFlightRef.current = false;
                        return;
                    }

                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const result = String(reader.result || '');
                        const base64 = result.includes(',') ? result.split(',')[1] : '';

                        onFrameCallback(base64);
                        frameInFlightRef.current = false;
                    };
                    reader.readAsDataURL(blob);
                }, 'image/jpeg', 0.80);
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
