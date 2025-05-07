
import React from 'react';

const steps = [
  {
    number: "01",
    title: "Create Your Profile",
    description: "Tell us what you're looking for - neighborhoods, price range, number of bedrooms, and must-have amenities.",
  },
  {
    number: "02",
    title: "We Monitor Listings",
    description: "Our system continuously scans Craigslist and other platforms for new listings that match your criteria.",
  },
  {
    number: "03",
    title: "Get Instant Alerts",
    description: "Receive email notifications with curated listings that match your exact requirements.",
  },
  {
    number: "04",
    title: "Contact & Secure",
    description: "Be the first to respond to new listings and increase your chances of securing your dream apartment.",
  }
];

const HowItWorks = () => {
  return (
    <section id="how-it-works" className="bg-white py-16 md:py-24">
      <div className="container-section">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="heading-secondary mb-6">How ApartmentFinder Works</h2>
          <p className="text-lg text-gray-600">
            A simple process designed to save you time and help you find your perfect apartment faster
          </p>
        </div>
        
        <div className="relative">
          <div className="absolute hidden lg:block top-24 left-0 right-0 h-1 bg-gradient-to-r from-apartment-blue to-apartment-green"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step, index) => (
              <div 
                key={index} 
                className="relative animate-slide-up"
                style={{ animationDelay: `${index * 150}ms` }}
              >
                <div className="flex justify-center lg:justify-start mb-6">
                  <div className="flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-r from-apartment-blue to-apartment-green text-white font-bold relative z-10">
                    {step.number}
                  </div>
                </div>
                <h3 className="heading-tertiary mb-3 text-center lg:text-left">{step.title}</h3>
                <p className="text-gray-600 text-center lg:text-left">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default HowItWorks;
