import { Button } from "@/components/ui/button";

interface NavbarProps {
  onGetStartedClick?: () => void;
}

const Navbar = ({ onGetStartedClick }: NavbarProps) => {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center">
          <a href="/" className="text-2xl font-bold text-apartment-blue flex items-center">
            <span className="text-apartment-green">Apartment</span>Finder
          </a>
        </div>
        <nav className="hidden md:flex items-center space-x-4 ml-auto pr-8">
          <a href="/welcome#features" className="text-sm font-medium hover:text-apartment-blue transition-colors">Features</a>
          <a href="/welcome#how-it-works" className="text-sm font-medium hover:text-apartment-blue transition-colors">How It Works</a>
          <a href="/welcome#pricing" className="text-sm font-medium hover:text-apartment-blue transition-colors">Pricing</a>
          <a href="/welcome#faq" className="text-sm font-medium hover:text-apartment-blue transition-colors">FAQ</a>
        </nav>
        <div className="flex items-center space-x-2">
          <Button variant="outline" className="hidden md:inline-flex" onClick={onGetStartedClick}>Log in</Button>
          <Button className="bg-apartment-blue hover:bg-blue-600 transition-colors" onClick={onGetStartedClick}>Sign up</Button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
