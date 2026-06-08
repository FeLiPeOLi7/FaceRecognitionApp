import { useState } from 'react';
import TextInput from './TextInput';
import ConsentCheckbox from './ConsentCheckbox';
import FileInput from './FileInput';
import VideoInput from './VideoInput';
import RegisterModeSelector from './RegisterModeSelector';
import styles from '../../styles/Register.module.css';

export default function RegisterForm({ name, onNameChange, consent, onConsentChange, onFileChange, onSubmit }) {
    const [insertMode, setInsertMode] = useState('file'); // 'file' or 'video'

    const handleModeChange = (mode) => {
        setInsertMode(mode);
        onFileChange(null);
    };

    return (
        <form onSubmit={onSubmit} className={styles.form}>
            <TextInput 
                label="Nome Completo:"
                value={name}
                onChange={onNameChange}
                required
            />
            <ConsentCheckbox
                checked={consent}
                onChange={onConsentChange}
            />

            <div className={styles.modeContainer}>
                <RegisterModeSelector
                    mode={insertMode}
                    onModeChange={handleModeChange}
                />

                {insertMode === 'file' ? (
                    <FileInput
                        label="Upload da Face (.png/.jpg):"
                        accept="image/*"
                        onChange={(e) => onFileChange(e.target.files[0])}
                        required
                    />
                ) : (
                        <VideoInput 
                            onFrameCaptured={onFileChange}
                        />
                    )}
            </div>
            <button type="submit" className={styles.submitButton}>
                Finalizar Cadastro
            </button>
        </form>
    );
}
