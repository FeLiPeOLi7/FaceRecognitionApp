import spinner from '../../assets/spinner.svg';
import styles from '../../styles/Recognize.module.css';

export default function VideoDisplay({ imageSrc }) {
    return (
        <div className={styles.displayWrapper}>
            <img 
                src={imageSrc || spinner}
                alt="Feedback do Servidor"
                className={styles.processedImage}
            />
            {!imageSrc ? <p className={styles.displayText}>Aguardando inicialização...</p> : <></>}
        </div>
    );
}
