import React from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import Pricing from '../components/Pricing';
import Testimonials from '../components/Testimonials';
import FAQ from '../components/FAQ';
import Footer from '../components/Footer';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleHeroAction = () => {
    if (isAuthenticated) {
      navigate('/overview');
    } else {
      navigate('/signin');
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar onGetStartedClick={handleHeroAction} />
      <div className="bg-background">
        <Hero onGetStartedClick={handleHeroAction} />
      </div>
      <div className="bg-apartment-light">
        <Features />
      </div>
      <div className="bg-background">
        <HowItWorks />
      </div>
      <div className="bg-apartment-light">
        <Pricing />
      </div>
      <div className="bg-background">
        <Testimonials />
      </div>
      <div className="bg-apartment-light">
        <FAQ />
      </div>
      <Footer />
    </div>
  );
};

export default Home;
