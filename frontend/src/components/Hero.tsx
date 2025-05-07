import React from 'react';
import { Button } from "@/components/ui/button";

interface HeroProps {
  onGetStartedClick?: () => void;
}

const Hero: React.FC<HeroProps> = ({ onGetStartedClick }) => {
  return (
    <section className="relative bg-white overflow-hidden">
      <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80')] bg-cover bg-center opacity-10"></div>
      <div className="container-section relative">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="animate-fade-in">
            <h1 className="heading-primary mb-6">
              Never Miss Your <span className="text-apartment-blue">Dream Apartment</span> Again
            </h1>
            <p className="text-xl mb-8 text-gray-600">
              ApartmentFinder monitors Craigslist and other listing sites 24/7 and delivers the best matches straight to your inbox, so you can be the first to respond.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button 
                className="bg-apartment-blue hover:bg-blue-600 text-lg px-8 py-6" 
                size="lg"
                onClick={onGetStartedClick}
              >
                Get Started Free
              </Button>
              <Button variant="outline" size="lg" className="text-lg px-8 py-6">
                How It Works
              </Button>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              No credit card required. Free 14-day trial.
            </p>
          </div>
          <div className="relative lg:h-[600px] flex items-center justify-center animate-fade-in">
            <div className="absolute inset-0 bg-gradient-to-r from-apartment-blue/20 to-apartment-green/20 rounded-3xl transform rotate-3"></div>
            <img
              src="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?ixlib=rb-4.0.3&auto=format&fit=crop&w=1950&q=80"
              alt="Apartment hunting made easy"
              className="rounded-2xl shadow-xl -rotate-2 relative w-full h-full object-cover"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
