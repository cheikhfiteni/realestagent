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
      navigate('/signin');
    }
  };

  return (
    <div className="min-h-screen">
      <Navbar onGetStartedClick={handleHeroAction} />
      <Hero onGetStartedClick={handleHeroAction} />
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
