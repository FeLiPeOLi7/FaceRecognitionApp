import styles from '../../styles/Register.module.css';

// Standardized single field form validation block
export default function TextInput({ label, value, onChange, required }) {
    return (
        <div className={styles.fieldGroup}>
            <label className={styles.label}>{label}</label>
            <input
                type="text"
                value={value}
                onChange={onChange}
                required={required}
                className={styles.inputText}
            />
        </div>
    );
}
