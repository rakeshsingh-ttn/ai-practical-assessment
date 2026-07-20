import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api, clearToken, getToken, setToken, setUnauthorizedHandler } from '../api/client';

const UserContext = createContext(null);

export function UserProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const logout = useCallback(() => {
    clearToken();
    setCurrentUser(null);
    setUsers([]);
    setError(null);
  }, []);

  const loadSession = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setCurrentUser(null);
      setUsers([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [me, allUsers] = await Promise.all([api.me(), api.getUsers()]);
      setCurrentUser(me);
      setUsers(allUsers);
    } catch (err) {
      clearToken();
      setCurrentUser(null);
      setUsers([]);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setCurrentUser(null);
      setUsers([]);
    });
    loadSession();
  }, [loadSession]);

  const login = async (email, password) => {
    setError(null);
    const { access_token: accessToken } = await api.login(email, password);
    setToken(accessToken);
    await loadSession();
  };

  return (
    <UserContext.Provider
      value={{
        currentUser,
        users,
        loading,
        error,
        isAuthenticated: Boolean(currentUser),
        login,
        logout,
        reloadSession: loadSession,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  return useContext(UserContext);
}
