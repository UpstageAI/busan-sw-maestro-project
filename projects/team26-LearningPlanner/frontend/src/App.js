import { useState } from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import Navbar from './StartPageComponents/Navbar';
import HeroSection from './StartPageComponents/HeroSection';
import MainPage from './mainComponents/MainPage';

function HomePage() {
  const navigate = useNavigate();
  const [isExiting, setIsExiting] = useState(false);

  const handleNavigateToPlanner = () => {
    setIsExiting(true);
    setTimeout(() => navigate('/planner'), 300);
  };

  return (
    <div className={`app-wrapper${isExiting ? ' exiting' : ''}`}>
      <div className="hero-gradient" />
      <div className="grain-texture" />
      <Navbar />
      <main className="main-content">
        <HeroSection onNavigateToPlanner={handleNavigateToPlanner} />
      </main>
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/planner" element={<MainPage />} />
    </Routes>
  );
}

export default App;
