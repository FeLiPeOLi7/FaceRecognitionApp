import styles from '../../styles/Register.module.css';

export default function RegisterModeSelector({ mode, onModeChange }) {
    return (
        <div className={styles.modeSelector}>
            <button
                type="button"
                className={`${styles.modeButton} ${mode === 'file' ? styles.modeButtonActive : ''}`}
                onClick={() => onModeChange('file')}
            >
                Upload de Arquivo
            </button>
            <button
                type="button"
                className={`${styles.modeButton} ${mode === 'video' ? styles.modeButtonActive : ''}`}
                onClick={() => onModeChange('video')}
            >
                Capturar via Câmera
            </button>
        </div>
    );
}
