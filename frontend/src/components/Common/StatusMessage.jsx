import styles from '../../styles/Common.module.css';

// Reactive status banner rendering system messages and inline network logging feedback
export default function StatusMessage({ message }) {
    if (!message) return null;
    return (
        <p className={styles.statusMessage}>{message}</p>
    )
}
