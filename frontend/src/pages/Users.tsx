import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Users: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const response = await axios.get('/api/persons');
        setUsers(response.data.items);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch users.');
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>{error}</div>;
  }

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Users</h2>
      <table className="min-w-full bg-white">
        <thead>
          <tr>
            <th className="py-2 px-4 border-b">Name</th>
            <th className="py-2 px-4 border-b">Phone</th>
            <th className="py-2 px-4 border-b">Consent</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id}>
              <td className="py-2 px-4 border-b">{user.name || user.id}</td>
              <td className="py-2 px-4 border-b">{user.phone || ''}</td>
              <td className="py-2 px-4 border-b">{user.consent ? 'Yes' : 'No'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Users;