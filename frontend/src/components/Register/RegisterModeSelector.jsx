import styles from '../../styles/Register.module.css';

export default function RegisterModeSelector({ mode, onModeChange }) {
    return (
        <div className={styles.modeSelector}>
            <button
                type="button"
                className={mode === 'file' ? styles.modeButtonActive : styles.modeButton}
                onClick={() => onModeChange('file')}
            >
                Upload de Arquivo
            </button>
            <button
                type="button"
                className={mode === 'video' ? styles.modeButtonActive : styles.modeButton}
                onClick={() => onModeChange('video')}
            >
                Capturar via Câmera
            </button>
        </div>
    );
}
