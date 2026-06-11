import { useState } from 'react';
import PageWrapper from '../Common/PageWrapper';
import Card from '../Common/Card';
import RegisterForm from './RegisterForm';
import StatusMessage from '../Common/StatusMessage';
import BackButton from '../Common/BackButton';
import { getFlaskBackendUrl } from '../../config/backendUrl';
import styles from '../../styles/Register.module.css';

// Boundary controller packaging identity metadata strings and raw files into structured form payloads
export default function RegisterContainer({ onNavigate }) {
    const [name, setName] = useState('');
    const [consent, setConsent] = useState(false);
    const [image, setImage] = useState(null);
    const [status, setStatus] = useState('');

    // Intercept form submission, validate local constraints, and fire network requests
    const handleFormSubmit = async (e) => {
        e.preventDefault();
        if (!consent) {
            setStatus('Erro: O consentimento biométrico é obrigatório sob conformidade legal.');
            return;
        }

        if (!image) {
            setStatus('Erro: Forneça uma imagem via upload ou captura de vídeo.');
            return;
        }

        // Multipart payload compilation required to send binary payloads with raw strings to REST API
        setStatus('Transmitindo payload para processamento...'); const formData = new FormData();
        formData.append('name', name);
        formData.append('consent', consent);
        formData.append('image', image);

        console.log("Name: " + name);
        console.log("Consent: " + consent);
        console.log(image);

        try {
            // Send multipart body to Flask REST registration endpoint
            const response = await fetch(`${getFlaskBackendUrl()}/registered`, {
                method: 'POST',
                body: formData, // The browser will handle automatic boundary injection
            });

            console.log(response)

            if (response.ok) {
                // Wipe form variables upon transaction success
                setStatus('Registro concluído! Face registrada');
                setName('');
                setConsent(false);
                setImage(null);
            } else {
                setStatus('Erro! Nenhuma face detectada');
            }
        } catch (err) {
            console.error(err);
            setStatus('Falha crítica de comunicação com o backend');
        }
    };

    return (
        <PageWrapper>
            <Card>
                <h2 className={styles.title}>Cadastro de Clientes</h2>
                <RegisterForm 
                    name={name}
                    onNameChange={(e) => setName(e.target.value)}
                    consent={consent}
                    onConsentChange={(e) => setConsent(e.target.checked)}
                    onFileChange={(file) => setImage(file)}
                    onSubmit={handleFormSubmit}
                />
                <StatusMessage message={status} />
                <BackButton onClick={() => onNavigate('home')} label="Voltar ao Menu Principal" />
            </Card>
        </PageWrapper>
    );
}
