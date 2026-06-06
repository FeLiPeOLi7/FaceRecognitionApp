import styles from '../../styles/Register.module.css';

export default function ConsentCheckbox({ checked, onChange }) {
    return (
        <div className={styles.checkboxGroup}>
            <input
                type="checkbox"
                id="consent-check"
                checked={checked}
                onChange={onChange}
                required
            />
            <label htmlFor="consent-check" className={styles.checkboxLabel}>
                Eu consinto explicitamente com o armazenamento e processamento regulamentado
                dos meus dados biométricos faciais em conformidade com as diretrizes da LGPD.
            </label>
        </div>
    );
}
