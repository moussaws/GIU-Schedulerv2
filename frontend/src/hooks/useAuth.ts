import { useState, useEffect, createContext, useContext, ReactNode } from 'react';
import { useQuery } from 'react-query';
import { User, LoginRequest, Token } from '../types';
import apiService from '../services/api';
import toast from 'react-hot-toast';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    // If we're not in the provider, return a hook that checks localStorage
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
      !!localStorage.getItem('access_token')
    );
    const [isLoading, setIsLoading] = useState(false);

    const { data: user } = useQuery<User>(
      'currentUser',
      () => apiService.getCurrentUser(),
      {
        enabled: isAuthenticated,
        retry: false,
        onError: () => {
          setIsAuthenticated(false);
          localStorage.removeItem('access_token');
        }
      }
    );

    const login = async (credentials: LoginRequest): Promise<boolean> => {
      setIsLoading(true);
      try {
        const tokenResponse = await apiService.login(credentials);
        localStorage.setItem('access_token', tokenResponse.access_token);
        setIsAuthenticated(true);
        toast.success('Login successful');
        return true;
      } catch (error: any) {
        toast.error(error.response?.data?.detail || 'Login failed');
        return false;
      } finally {
        setIsLoading(false);
      }
    };

    const logout = () => {
      localStorage.removeItem('access_token');
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    };

    return {
      user: user || null,
      isAuthenticated,
      isLoading,
      login,
      logout
    };
  }
  return context;
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const auth = useAuth();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
};