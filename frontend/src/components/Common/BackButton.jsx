import styles from '../../styles/Common.module.css';

// Navigation action button targeting back-to-menu routing transitions
export default function BackButton({ onClick, label = "Voltar" }) {
    return (
        <button type="button" onClick={onClick} className={styles.backButton}>
            {label}
        </button>
    );
}
