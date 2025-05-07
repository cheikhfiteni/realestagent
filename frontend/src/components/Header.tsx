import { useNavigate } from 'react-router-dom';

function Header() {
  const navigate = useNavigate();

  return (
    <div 
      onClick={() => navigate('/welcome')} 
      className="flex items-center gap-2 cursor-pointer delayed-fade-in"
    >
      <img src="/placeholder-logo.svg" alt="Logo" className="w-8 h-8" />
      <span className="text-xl font-semibold font-serif">ApartmentFinder</span>
    </div>
  );
}

export default Header;