import styles from '../../styles/Home.module.css';

// Static titles presenting global contextual system labeling
export default function HomeHeader() {
    return (
        <>
            <h1 className={styles.title}>Detector Facial</h1>
            <p className={styles.subtitle}>Escolha uma opção para continuar:</p>
        </>
    );
}
