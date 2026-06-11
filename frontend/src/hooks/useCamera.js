import { useRef, useState } from 'react';

export function useCamera(fps = 5) {
    const [capturing, setCapturing] = useState(false); // Track active camera streaming state
    const [status, setStatus] = useState('Pronto'); // UI status feedback

    const streamRef = useRef(null); // Store the active MediaStream instance
    const timerIdRef = useRef(null); // Reference to the active setInterval clock
    const frameInFlightRef = useRef(false); // Synchronization flag to prevent canvas processing overlaps

    const videoElementRef = useRef(null); // Ref to hidden video element fed by webcam
    const canvasElementRef = useRef(null); // Ref to offscreen canvas used for frame capture

    const intervalMs = Math.max(1000 / fps, 120); // Safe processing rate ceiling

    // Clean up interval clocks, media tracks, and clear stat
    const stopCapture = () => {
        if (timerIdRef.current)
            clearInterval(timerIdRef.current);

        timerIdRef.current = null;
        frameInFlightRef.current = false;

        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop()); // Terminate hardware stream
            streamRef.current = null;
        }

        setCapturing(false);
        setStatus('Parado');
    };

    // Request webcam access, match screen orientation, and initialize frame capture loop
    const startCapture = async (onFrameCallback) => {
        if (streamRef.current) return;

        setStatus('Iniciando câmera...');
        try {
            // Dynamic payload engineering: Adapt resolution based on viewport orientation
            const isMobilePortrait = window.innerHeight > window.innerWidth;
            const constraints = {
                video: {
                    width: isMobilePortrait ? { ideal: 720 } : { ideal: 1280 },
                    height: isMobilePortrait ? { ideal: 1280 } : { ideal: 720 },
                    facingMode: 'user', // Force front-facing camera on mobile devices
                },
                audio: false,
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            streamRef.current = stream;

            if (videoElementRef.current) {
                videoElementRef.current.srcObject = stream;
            }

            // Await metadata loading to read actual resolution allocated by hardware
            await new Promise((resolve) => {
                if (videoElementRef.current) {
                    videoElementRef.current.onloadedmetadata = () => resolve();
                } else {
                    resolve();
                }
            });

            // Extract the true dimensions delivered by the active video track
            const videoTrack = stream.getVideoTracks()[0];
            const { width: realWidth, height: realHeight } = videoTrack.getSettings();

            // Match internal canvas buffer dimension to video source
            if (canvasElementRef.current) {
                canvasElementRef.current.width = realWidth;
                canvasElementRef.current.height = realHeight;
            }

            setCapturing(true);
            setStatus(`Capturando video`);

            const ctx = canvasElementRef.current.getContext('2d');

            // Match internal canvas buffer dimension to video source 1:1
            timerIdRef.current = setInterval(() => {
                if (
                    !streamRef.current || 
                        frameInFlightRef.current || 
                        !videoElementRef.current || 
                        videoElementRef.current.readyState < 2 // Ensure video data is ready for drawing
                ) return;

                frameInFlightRef.current = true; // Lock frame until serialization completes

                // Snap current frame from video element onto context matrix
                ctx.drawImage(videoElementRef.current, 0, 0, realWidth, realHeight);

                // Compress frame matrix into binary JPEG blob at 80% quality to optimize network bandwidth
                canvasElementRef.current.toBlob((blob) => {
                    if (!blob) {
                        frameInFlightRef.current = false;
                        return;
                    }

                    // Convert binary image payload into network-safe ASCII Base64 string
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const result = String(reader.result || '');
                        // Strip metadata prefix (e.g., "data:image/jpeg;base64,") to yield clean data
                        const base64 = result.includes(',') ? result.split(',')[1] : '';

                        onFrameCallback(base64); // Fire payload over the custom socket channel
                        frameInFlightRef.current = false; // Release lock for next available tick
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
