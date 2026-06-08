import styles from '../../styles/Common.module.css';

export default function PageWrapper({ children }) {
    return (
        <div className={styles.pageWrapper}>
            {children}
        </div>
    );
}
