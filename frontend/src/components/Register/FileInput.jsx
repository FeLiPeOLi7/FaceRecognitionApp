import styles from '../../styles/Register.module.css';

export default function FileInput({ label, accept, onChange, required }) {
    return (
        <div className={styles.fieldGroup}>
            <label className={styles.label}>{label}</label>
            <input
                type="file"
                accept={accept}
                onChange={onChange}
                required={required}
            />
        </div>
    );
}
