import React from 'react';

const About: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div className="space-y-12">
        <h1 className="text-5xl font-extrabold tracking-tight text-gray-900 sm:text-6xl text-center">
          Why Spending (Time) On Housing Matters
        </h1>
        <div className="prose prose-xl text-gray-700 mx-auto">
            <p style={{ textIndent: "30px", paddingLeft: "5px", paddingRight: "5px" }} className="text-xl leading-relaxed mb-8">
              Housing is everything. On average, you'll spend <span className="font-semibold">4,380 hours</span> a year in your apartment. You'll call it home for 474 days and invest 30% of your income into maintaining it. Yet, on average, most people only spend 2-4 hours searching for their next rental.
            </p>
            <p style={{ textIndent: "30px", paddingLeft: "5px", paddingRight: "5px" }} className="text-xl leading-relaxed">
              The difference between renting a good and great home is immense. And the key determinant is time. <em>That's where we come in.</em> <span className="font-semibold">ApartmentFinder</span> keeps an eye on the market 24/7, so you don't have to. Simply tell us your criteria, budget, and preferred locations—we'll run sophisticated searches throughout the day and deliver the best matches straight to your inbox. All this for just <span className="font-semibold">$5/month</span>. 
            </p>
        </div>
      </div>
    </div>
  );
};

export default About;