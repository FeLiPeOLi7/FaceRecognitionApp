import { useEffect } from 'react';
import PageWrapper from '../Common/PageWrapper';
import Card from '../Common/Card';
import VideoDisplay from './VideoDisplay';
import VideoCanvasHidden from './VideoCanvasHidden';
import CameraControls from './CameraControls';
import StatusMessage from '../Common/StatusMessage';
import { useCamera } from '../../hooks/useCamera';
import { useSocket } from '../../hooks/useSocket';
import styles from '../../styles/Recognize.module.css';

// Controller managing live camera hooks and polling network emitters
export default function RecognizeContainer({ onNavigate }) {
    const { emitFrame, processedSrc, socketError } = useSocket();
    const {
        capturing,
        status,
        setStatus,
        startCapture,
        stopCapture,
        videoElementRef,
        canvasElementRef
    } = useCamera(5); // Throttle tracking tick frame dispatch to 5 FPS

    // Component lifecycle teardown: Force secure resource clearance on unmount
    useEffect(() => {
        return () => stopCapture();
    }, []);

    // Network error listener: Synchronize socket degradation state directly into user interface
    useEffect(() => {
        if (socketError) {
            setStatus('Erro de conexão com o barramento WebSockets.');
        }
    }, [socketError]);

    // Feed target tick callback to bind live frame Base64 strings straight into the network emitter
    const handleStart = () => {
        startCapture((base64Frame) => {
            emitFrame(base64Frame);
        });
    };

    return (
        <PageWrapper>
            <Card isLarge={true}>
                <h1 className={styles.title}>Reconhecimento Facial</h1>

                <VideoCanvasHidden videoRef={videoElementRef} canvasRef={canvasElementRef} />
                <VideoDisplay imageSrc={processedSrc} />

                <StatusMessage message={`Status: ${status}`} />

                <CameraControls 
                    capturing={capturing} 
                    onStart={handleStart} 
                    onStop={stopCapture} 
                    onHome={() => onNavigate('home')} 
                />
            </Card>
        </PageWrapper>
    );
}
