
import React from 'react';
import { Mail, Search, ArrowRight, MapPin } from "lucide-react";

const features = [
  {
    title: "Real-time Monitoring",
    description: "Our system scans apartment listings across multiple platforms every 15 minutes, ensuring you're always up-to-date.",
    icon: <Search className="h-12 w-12 text-apartment-blue" />
  },
  {
    title: "Smart Filtering",
    description: "Set your preferences once and let our AI find apartments that match your exact requirements - location, price, size, and amenities.",
    icon: <MapPin className="h-12 w-12 text-apartment-green" />
  },
  {
    title: "Instant Alerts",
    description: "Get email notifications the moment a perfect match is found, giving you a head start over other apartment hunters.",
    icon: <Mail className="h-12 w-12 text-apartment-blue" />
  },
  {
    title: "Multiple Sources",
    description: "We don't just check Craigslist - we scan dozens of listing sites to ensure you never miss an opportunity.",
    icon: <ArrowRight className="h-12 w-12 text-apartment-green" />
  }
];

const Features = () => {
  return (
    <section id="features" className="bg-apartment-light py-16 md:py-24">
      <div className="container-section">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="heading-secondary mb-6">All the Tools You Need to Find Your Perfect Home</h2>
          <p className="text-lg text-gray-600">
            Stop refreshing listing pages all day and let ApartmentFinder do the heavy lifting
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-12">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-shadow animate-slide-up"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <div className="mb-6">{feature.icon}</div>
              <h3 className="heading-tertiary mb-3">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
