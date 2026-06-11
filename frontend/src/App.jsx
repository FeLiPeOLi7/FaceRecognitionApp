import { useState } from 'react';
import HomeContainer from './components/Home/HomeContainer';
import RegisterContainer from './components/Register/RegisterContainer';
import RecognizeContainer from './components/Recognize/RecognizeContainer';

export default function App() {
    // Abstract client-side state router to handle core screen navigation
    const [currentRoute, setCurrentRoute] = useState('home');

    // Conditional switch execution guarding layout wrapper mountings
    switch (currentRoute) {
        case 'register':
            return <RegisterContainer onNavigate={setCurrentRoute} />;
        case 'recognize':
            return <RecognizeContainer onNavigate={setCurrentRoute} />;
        case 'home':
            return <HomeContainer onNavigate={setCurrentRoute} />;
    }
}
