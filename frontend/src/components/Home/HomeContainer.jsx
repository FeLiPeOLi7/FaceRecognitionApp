import PageWrapper from '../Common/PageWrapper';
import Card from '../Common/Card';
import HomeHeader from './HomeHeader';
import HomeButton from './HomeButton';

export default function HomeContainer({ onNavigate }) {
    return (
        <PageWrapper>
            <Card>
                <HomeHeader />
                <HomeButton 
                    label="Registrar Face"
                    variant="register"
                    onClick={() => onNavigate('register')} 
                />
                <HomeButton 
                    label="Reconhecer Face" 
                    variant="recognize" 
                    onClick={() => onNavigate('recognize')} 
                />
            </Card>
        </PageWrapper>
    );
}
