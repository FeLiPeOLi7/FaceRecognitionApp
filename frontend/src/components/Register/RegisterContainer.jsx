import { useState } from 'react';
import PageWrapper from '../Common/PageWrapper';
import Card from '../Common/Card';
import RegisterForm from './RegisterForm';
import StatusMessage from '../Common/StatusMessage';
import BackButton from '../Common/BackButton';
import { getBackendUrl } from '../../config/backendUrl';
import styles from '../../styles/Register.module.css';

export default function RegisterContainer({ onNavigate }) {
    const [name, setName] = useState('');
    const [consent, setConsent] = useState(false);
    const [image, setImage] = useState(null);
    const [status, setStatus] = useState('');

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

        setStatus('Transmitindo payload para processamento...');
        const formData = new FormData();
        formData.append('name', name);
        formData.append('consent', consent);
        formData.append('image', image);

        console.log("Name: " + name);
        console.log("Consent: " + consent);
        console.log(image);

        try {
            const response = await fetch(`${getBackendUrl()}/registered`, {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                setStatus('Registro concluído! Face registrada');
                setName('');
                setConsent(false);
                setImage(null);
            } else {
                setStatus('Erro na persistência do cadastro no servidor.');
            }
        } catch (err) {
            console.error(err);
            setStatus('Falha crítica de comunicação com o backend.');
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
