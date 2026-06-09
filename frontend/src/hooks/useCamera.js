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
            // 1. ENGENHARIA DE PAYLOAD: Detecta orientação para definir a resolução ideal
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

            // Aguarda o vídeo carregar os metadados para sabermos o tamanho real entregue pelo hardware
            await new Promise((resolve) => {
                if (videoElementRef.current) {
                    videoElementRef.current.onloadedmetadata = () => resolve();
                } else {
                    resolve();
                }
            });

            // 2. DIMENSIONAMENTO DINÂMICO: Extrai o tamanho real do track de vídeo
            const videoTrack = stream.getVideoTracks()[0];
            const { width: realWidth, height: realHeight } = videoTrack.getSettings();

            // Ajusta o Canvas interno para ter a mesma resolução real da câmera
            if (canvasElementRef.current) {
                canvasElementRef.current.width = realWidth;
                canvasElementRef.current.height = realHeight;
            }

            setCapturing(true);
            setStatus(`Capturando video`);

            const ctx = canvasElementRef.current.getContext('2d');

            // Loop de ticks (FPS) via setInterval
            timerIdRef.current = setInterval(() => {
                if (
                    !streamRef.current || 
                        frameInFlightRef.current || 
                        !videoElementRef.current || 
                        videoElementRef.current.readyState < 2
                ) return;

                frameInFlightRef.current = true;

                // Desenha a matriz do frame respeitando a resolução real do sensor
                ctx.drawImage(videoElementRef.current, 0, 0, realWidth, realHeight);

                // Serialização e envio do Payload binário convertido em Base64
                canvasElementRef.current.toBlob((blob) => {
                    if (!blob) {
                        frameInFlightRef.current = false;
                        return;
                    }

                    const reader = new FileReader();
                    reader.onloadend = () => {
                        const result = String(reader.result || '');
                        const base64 = result.includes(',') ? result.split(',')[1] : '';

                        // Callback que dispara o evento pelo canal do Socket.IO
                        onFrameCallback(base64);
                        frameInFlightRef.current = false;
                    };
                    reader.readAsDataURL(blob);
                }, 'image/jpeg', 0.80); // Compressão em 80% de qualidade para otimizar vazão de rede
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
