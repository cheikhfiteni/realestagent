
import React from 'react';
import { Card, CardContent } from "@/components/ui/card";

const testimonials = [
  {
    quote: "ApartmentFinder helped me secure my dream apartment in a competitive market. I got an alert and was the first person to contact the landlord!",
    author: "Sarah Johnson",
    title: "Designer in New York",
    avatar: "https://i.pravatar.cc/100?img=1"
  },
  {
    quote: "I was spending hours refreshing Craigslist every day. ApartmentFinder automated everything and found me a great place within a week.",
    author: "Michael Chen",
    title: "Software Engineer in San Francisco",
    avatar: "https://i.pravatar.cc/100?img=3"
  },
  {
    quote: "The filtering is incredible. I set up my preferences once, and every listing I received was exactly what I was looking for.",
    author: "Emma Rodriguez",
    title: "Marketing Manager in Chicago",
    avatar: "https://i.pravatar.cc/100?img=5"
  },
];

const Testimonials = () => {
  return (
    <section className="bg-white py-16 md:py-24">
      <div className="container-section">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="heading-secondary mb-6">What Our Users Say</h2>
          <p className="text-lg text-gray-600">
            Join thousands of satisfied apartment hunters who found their perfect home with our help
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <Card 
              key={index}
              className="animate-slide-up border border-gray-100"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              <CardContent className="pt-6">
                <div className="flex flex-col items-center text-center">
                  <div className="relative mb-6">
                    <div className="absolute inset-0 bg-gradient-to-r from-apartment-blue to-apartment-green rounded-full blur-[1px] scale-110 opacity-30"></div>
                    <img 
                      src={testimonial.avatar} 
                      alt={testimonial.author}
                      className="w-16 h-16 rounded-full border-2 border-white relative z-10 object-cover"
                    />
                  </div>
                  <p className="text-gray-700 mb-6 italic">"{testimonial.quote}"</p>
                  <div>
                    <p className="font-bold">{testimonial.author}</p>
                    <p className="text-sm text-gray-500">{testimonial.title}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
