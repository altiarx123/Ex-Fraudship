import React from 'react';
import Button from './Button';

interface HeaderProps {
  status: string;
  locationPermission: boolean;
  darkMode: boolean;
  setDarkMode: (darkMode: boolean) => void;
}

const Header: React.FC<HeaderProps> = ({ status, locationPermission, darkMode, setDarkMode }) => {
  return (
    <header className={`p-4 ${darkMode ? 'bg-gray-800' : 'bg-white'} shadow`}>
      <div className="container mx-auto flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">E-X FraudShield</h1>
          <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Operational dashboard</div>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-sm" aria-live="polite">
            WS: <span className={`inline-block w-3 h-3 rounded-full ${status === 'open' ? 'bg-green-500' : 'bg-gray-400'}`} />
          </div>
          <div aria-live="polite">
            Location permission: <span className={`inline-block w-3 h-3 rounded-full ml-2 ${locationPermission ? 'bg-green-500' : 'bg-gray-400'}`}></span>
          </div>
          <Button onClick={() => setDarkMode(!darkMode)} className={`px-2 py-1 ml-2 text-sm rounded ${darkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
            {darkMode ? 'Light' : 'Dark'} Mode
          </Button>
        </div>
      </div>
    </header>
  );
};

export default Header;