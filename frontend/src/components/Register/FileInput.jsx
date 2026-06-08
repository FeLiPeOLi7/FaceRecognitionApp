import styles from '../../styles/Register.module.css';

export default function FileInput({ label, accept, onChange, required }) {
    return (
        <div className={styles.fieldGroup}>
            <h1 className={styles.label}>{label}</h1>
            <input
                type="file"
                accept={accept}
                onChange={onChange}
                required={required}
            />
        </div>
    );
}
