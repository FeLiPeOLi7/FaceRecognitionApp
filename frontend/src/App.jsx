import { useState } from 'react';
import HomeContainer from './components/Home/HomeContainer';
import RegisterContainer from './components/Register/RegisterContainer';
import RecognizeContainer from './components/Recognize/RecognizeContainer';

export default function App() {
    const [currentRoute, setCurrentRoute] = useState('home');

    switch (currentRoute) {
        case 'register':
            return <RegisterContainer onNavigate={setCurrentRoute} />;
        case 'recognize':
            return <RecognizeContainer onNavigate={setCurrentRoute} />;
        case 'home':
            return <HomeContainer onNavigate={setCurrentRoute} />;
    }
}
