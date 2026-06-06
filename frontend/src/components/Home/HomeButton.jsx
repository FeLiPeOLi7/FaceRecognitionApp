import styles from '../../styles/Home.module.css';

export default function HomeButton({ label, variant, onClick }) {
    const buttonClass = `${styles.button} ${variant === 'register' ? styles.register : styles.recognize}`;
    return (
        <button className={buttonClass} onClick={onClick}>
            {label}
        </button>
    );
}
