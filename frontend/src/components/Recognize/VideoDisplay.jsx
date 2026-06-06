import avatarSvg from '../../assets/avatar-placeholder.svg';
import styles from '../../styles/Recognize.module.css';

export default function VideoDisplay({ imageSrc }) {
    return (
        <div className={styles.displayWrapper}>
            <img 
                src={imageSrc || avatarSvg}
                alt="Feedback do Servidor"
                className={styles.processedImage}
            />
        </div>
    );
}
