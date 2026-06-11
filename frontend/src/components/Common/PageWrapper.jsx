import styles from '../../styles/Common.module.css';

// Main view boundary container handling viewport centering and structural padding resets
export default function PageWrapper({ children }) {
    return (
        <div className={styles.pageWrapper}>
            {children}
        </div>
    );
}
