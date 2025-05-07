import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Check } from "lucide-react";

const plans = [
  {
    name: "Basic",
    price: "Free",
    description: "For casual apartment hunters",
    features: [
      "One search profile",
      "Daily email updates",
      "Access to Craigslist listings",
      "Basic filtering options",
    ],
    buttonText: "Get Started",
    buttonVariant: "outline",
  },
  {
    name: "Premium",
    price: "$9.99",
    period: "/month",
    description: "For serious apartment hunters",
    features: [
      "Three search profiles",
      "Real-time email alerts",
      "Access to all listing sources",
      "Advanced filtering options",
      "Priority support",
      "Early bird notifications",
    ],
    buttonText: "Start Free Trial",
    buttonVariant: "default",
    highlighted: true,
  },
  {
    name: "Professional",
    price: "$29.99",
    period: "/month",
    description: "For real estate professionals",
    features: [
      "Unlimited search profiles",
      "Real-time email alerts",
      "Access to all listing sources",
      "Advanced filtering options",
      "Priority support",
      "Early bird notifications",
      "Listing analytics",
      "White-labeled emails",
    ],
    buttonText: "Contact Sales",
    buttonVariant: "outline",
  },
];

const Pricing = () => {
  return (
    <section id="pricing" className="bg-apartment-light py-16 md:py-24">
      <div className="container-section">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="heading-secondary mb-6">Simple, Transparent Pricing</h2>
          <p className="text-lg text-gray-600">
            Choose the plan that's right for you and start finding your dream apartment today
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <Card 
              key={index}
              className={`animate-slide-up ${
                plan.highlighted 
                  ? "border-apartment-blue shadow-lg shadow-blue-100 relative overflow-hidden" 
                  : ""
              }`}
              style={{ animationDelay: `${index * 150}ms` }}
            >
              {plan.highlighted && (
                <div className="absolute top-0 right-0">
                  <div className="bg-apartment-blue text-white text-xs font-bold px-3 py-1 transform translate-x-2 -translate-y-1 rotate-45">
                    POPULAR
                  </div>
                </div>
              )}
              <CardHeader>
                <CardTitle className="text-2xl">{plan.name}</CardTitle>
                <div className="flex items-baseline mt-4">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  {plan.period && <span className="ml-1 text-gray-500">{plan.period}</span>}
                </div>
                <CardDescription className="mt-2">{plan.description}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex">
                      <Check className="h-5 w-5 text-apartment-green mr-2" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button 
                  className={`w-full ${
                    plan.buttonVariant === "default" 
                      ? "bg-apartment-blue hover:bg-blue-600" 
                      : ""
                  }`}
                  variant={plan.buttonVariant as any}
                >
                  {plan.buttonText}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Pricing;
