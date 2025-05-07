import React from 'react';
import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import Pricing from '../components/Pricing';
import Testimonials from '../components/Testimonials';
import FAQ from '../components/FAQ';
import Footer from '../components/Footer';
import { Auth } from '../components/Auth';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleHeroAction = () => {
    if (isAuthenticated) {
      navigate('/overview');
    } else {
      console.log('User not authenticated, showing Auth component needs to be implemented');
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar />
      <Hero onGetStartedClick={handleHeroAction} />
      {!isAuthenticated && (
        <div className="flex-grow flex items-center justify-center py-12">
          <Auth />
        </div>
      )}
      <Features />
      <HowItWorks />
      <Pricing />
      <Testimonials />
      <FAQ />
      <Footer />
    </div>
  );
};

export default Home;
