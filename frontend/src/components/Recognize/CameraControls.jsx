import CameraButton from './CameraButton';
import styles from '../../styles/Recognize.module.css';

export default function CameraControls({ capturing, onStart, onStop, onHome }) {
    return (
        <div className={styles.controlsRow}>
            <CameraButton label="Home" type="home" onClick={onHome} />
            <CameraButton label="Iniciar" type="start" onClick={onStart} disabled={capturing} />
            <CameraButton label="Parar" type="stop" onClick={onStop} disabled={!capturing} />
        </div>
    );
}
