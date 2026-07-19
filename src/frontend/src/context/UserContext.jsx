import { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [users, setUsers] = useState([]);
  const [currentUserId, setCurrentUserId] = useState(
    () => Number(localStorage.getItem('actingAsUserId')) || null
  );
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getUsers()
      .then((data) => {
        setUsers(data);
        if (!currentUserId && data.length > 0) {
          setCurrentUserId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (currentUserId) {
      localStorage.setItem('actingAsUserId', String(currentUserId));
    }
  }, [currentUserId]);

  const currentUser = users.find((u) => u.id === currentUserId) || null;

  return (
    <UserContext.Provider value={{ users, currentUser, currentUserId, setCurrentUserId, error }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
