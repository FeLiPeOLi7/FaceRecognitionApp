import styles from '../../styles/Recognize.module.css';

export default function CameraButton({ label, type, onClick, disabled }) {
    const btnClass = `${styles.btnControl} ${styles[type]}`;
    return (
        <button className={btnClass} onClick={onClick} disabled={disabled}>
            {label}
        </button>
    );
}
