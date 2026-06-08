import styles from '../../styles/Common.module.css';

export default function StatusMessage({ message }) {
    if (!message) return null;
    return (
        <p className={styles.statusMessage}>{message}</p>
    )
}
