import React from 'react';
import Button from './Button';

interface SidebarProps {
  tab: 'transactions' | 'bias' | 'logs' | 'users';
  setTab: (tab: 'transactions' | 'bias' | 'logs' | 'users') => void;
  darkMode: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ tab, setTab, darkMode }) => {
  const navItems = [
    { key: 'transactions', label: 'Transaction Check' },
    { key: 'bias', label: 'Bias Monitoring' },
    { key: 'logs', label: 'AI Governance Logs' },
    { key: 'users', label: 'Users' },
  ];

  return (
    <aside className={`p-4 rounded-lg ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
      <h2 className="text-lg font-semibold mb-4">Menu</h2>
      <nav className="flex flex-col gap-2">
        {navItems.map(item => (
          <Button
            key={item.key}
            onClick={() => setTab(item.key as 'transactions' | 'bias' | 'logs' | 'users')}
            className={`px-3 py-2 text-left rounded ${
              tab === item.key
                ? 'bg-blue-600 text-white'
                : darkMode
                ? 'bg-gray-700 hover:bg-gray-600'
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
          >
            {item.label}
          </Button>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;