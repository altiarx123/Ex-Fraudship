import React from 'react';
import Card from './Card';

interface DashboardProps {
  darkMode: boolean;
  eventsLength: number;
  locationPermission: boolean;
  setLocationPermission: (permission: boolean) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ darkMode, eventsLength, locationPermission, setLocationPermission }) => {
  return (
    <Card>
      <h3 className="font-semibold">Dashboard</h3>
      <div className="mt-2 grid grid-cols-2 gap-2">
        <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-50'} p-2 rounded text-center`}>
          Users<br/><strong>5</strong>
        </div>
        <div className={`${darkMode ? 'bg-gray-700' : 'bg-gray-50'} p-2 rounded text-center`}>
          Notifications<br/><strong>{eventsLength}</strong>
        </div>
      </div>
      <div className="mt-3">
        <label className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>Location permission</label>
        <div className="mt-1 flex items-center gap-2">
          <input id="locperm" type="checkbox" checked={locationPermission} onChange={e => setLocationPermission(e.target.checked)} />
          <label htmlFor="locperm" className="text-sm">Grant location permission</label>
        </div>
      </div>
    </Card>
  );
};

export default Dashboard;