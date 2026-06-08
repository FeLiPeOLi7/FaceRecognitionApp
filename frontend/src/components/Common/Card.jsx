import styles from '../../styles/Common.module.css';

export default function Card({ children, isLarge = false }) {
    return (
        <div className={`${styles.card} ${isLarge ? styles.cardLarge : styles.card}`}>
            {children}
        </div>
    );
}
