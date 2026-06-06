import { useRef, useState, useEffect } from 'react';
import styles from '../../styles/Register.module.css';

export default function VideoInput({ onFrameCaptured }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [hasSnapshot, setHasSnapshot] = useState(false);
    const streamRef = useRef(null);

    useEffect(() => {
        async function initCamera() {
            try {
                const mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: 640, height: 480, facingMode: 'user' },
                    audio: false
                });

                streamRef.current = mediaStream;

                if (videoRef.current) {
                    videoRef.current.srcObject = mediaStream;
                }
            } catch (err) {
                console.error("Erro ao acessar a câmera para registro:", err);
            }
        }

        initCamera();

        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const takeSnapshot = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        canvas.toBlob((blob) => {
            if (blob) {
                const file = new File([blob], "webcam_capture.png", { type: "image/png" });
                onFrameCaptured(file);
                setHasSnapshot(true);
            }
        }, 'image/png');
    };

    const resetSnapshot = () => {
        setHasSnapshot(false);
        onFrameCaptured(null);
    };

    return (
        <div className={styles.videoCaptureContainer}>
            <label className={styles.label}>Posicione seu rosto:</label>
            <div className={styles.cameraPreviewWrapper}>
                <video 
                    ref={videoRef} 
                    autoPlay 
                    playsInline 
                    className={styles.videoElement}
                    style={{ display: hasSnapshot ? 'none' : 'block' }}
                ></video>
                <canvas 
                    ref={canvasRef} 
                    className={styles.capturedCanvasPreview}
                    style={{ display: hasSnapshot ? 'block' : 'none' }}
                ></canvas>
            </div>

            {!hasSnapshot ? (
                <button type="button" onClick={takeSnapshot} className={styles.actionButtonPrimary}>
                    Tirar Foto
                </button>
            ) : (
                    <button type="button" onClick={resetSnapshot} className={styles.actionSecondary}>
                        Recapturar
                    </button>
                )}
        </div>
    );
}
