import { useRef, useState, useEffect } from 'react';
import styles from '../../styles/Register.module.css';

// Dedicated single-shot snapshot element for enrollment photography
export default function VideoInput({ onFrameCaptured }) {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [hasSnapshot, setHasSnapshot] = useState(false); // Controls view state freeze
    const streamRef = useRef(null);

    // Context initialization: Mount camera constraints targeting localized user frame bounds
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

        // Safe cleanup: Cut active hardware signals on component unmount
        return () => {
            if (streamRef.current) {
                streamRef.current.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    // Snap layout image matrix and package it into a formal file format mock
    const takeSnapshot = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

        // Copy exact native capture metrics from active hardware stream
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert the structural pixel map into a lossless PNG binary file configuration
        canvas.toBlob((blob) => {
            if (blob) {
                // Package raw bytes inside an actual File instance to fit multipart form requirements
                const file = new File([blob], "webcam_capture.png", { type: "image/png" });
                onFrameCaptured(file); // Bubble file back to core form state container
                setHasSnapshot(true);  // Freeze active layout rendering elements
            }
        }, 'image/png');
    };

    // Release layout lock flags and purge temporary file pointers
    const resetSnapshot = () => {
        setHasSnapshot(false);
        onFrameCaptured(null);
    };

    return (
        <div className={styles.videocapturecontainer}>
            <h1 className={styles.label}>Posicione seu rosto:</h1>
            <div className={styles.cameraPreviewWrapper}>
                {/* Dynamically hide/reveal elements using css rules to protect continuous capture loops */}
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

            <div className={styles.snapshotWrapper}>
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

        </div>
    );
}
