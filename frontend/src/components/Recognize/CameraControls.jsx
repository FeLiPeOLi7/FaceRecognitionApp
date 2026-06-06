import CameraButton from './CameraButton';
import styles from '../../styles/Recognize.module.css';

export default function CameraControls({ capturing, onStart, onStop, onHome }) {
    return (
        <div className={styles.controlsRow}>
            <CameraButton label="Home" type="home" onClick={onHome} />
            <CameraButton label="Start" type="start" onClick={onStart} disabled={capturing} />
            <CameraButton label="Stop" type="stop" onClick={onStop} disabled={!capturing} />
        </div>
    );
}
