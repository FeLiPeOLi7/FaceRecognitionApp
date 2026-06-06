import styles from '../../styles/Common.module.css';

export default function BackButton({ onClick, label = "Voltar" }) {
    return (
        <button type="button" onClick={onClick} className={styles.backButton}>
            {label}
        </button>
    );
}
