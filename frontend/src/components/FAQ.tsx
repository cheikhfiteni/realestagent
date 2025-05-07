
import React from 'react';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqs = [
  {
    question: "How often are new listings checked?",
    answer: "ApartmentFinder scans for new listings every 15 minutes across all supported platforms. This ensures you're among the first to know when a new apartment matching your criteria becomes available."
  },
  {
    question: "Which listing sites do you monitor?",
    answer: "We monitor Craigslist, Zillow, Apartments.com, Trulia, HotPads, and many other popular apartment listing websites. Our comprehensive coverage ensures you don't miss any potential matches."
  },
  {
    question: "How do I set up my search preferences?",
    answer: "After signing up, you'll be guided through a simple onboarding process where you can specify your desired neighborhoods, price range, number of bedrooms, and must-have amenities. You can update these preferences anytime."
  },
  {
    question: "Is there a limit to how many alerts I can receive?",
    answer: "Basic users receive a daily digest of new listings. Premium and Professional users receive real-time alerts with no limit on the number of notifications."
  },
  {
    question: "Can I pause notifications temporarily?",
    answer: "Yes, you can easily pause and resume notifications from your dashboard at any time. This is useful when you're traveling or taking a break from your apartment search."
  },
  {
    question: "Do you offer refunds?",
    answer: "We offer a 14-day money-back guarantee for all paid plans. If you're not satisfied with our service within the first 14 days, we'll provide a full refund, no questions asked."
  },
];

const FAQ = () => {
  return (
    <section id="faq" className="bg-apartment-light py-16 md:py-24">
      <div className="container-section">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="heading-secondary mb-6">Frequently Asked Questions</h2>
          <p className="text-lg text-gray-600">
            Got questions? We've got answers. If you can't find what you're looking for, please contact our support team.
          </p>
        </div>
        
        <div className="max-w-3xl mx-auto">
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`item-${index}`}>
                <AccordionTrigger className="text-left">{faq.question}</AccordionTrigger>
                <AccordionContent>
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </div>
    </section>
  );
};

export default FAQ;
