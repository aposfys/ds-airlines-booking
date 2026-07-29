import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await api.post('/auth/login', { username, password });
      // Awaited: login now fetches the profile from /auth/me, and navigating
      // before it resolves lands on the dashboard with a null user.
      await login(response.data.access_token);
      navigate('/dashboard');
    } catch {
      setError('That username and password do not match. Check both and try again.');
    }
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-accent font-sans">
      {/* Visual Side */}
      <div className="hidden md:flex flex-col justify-center items-center w-1/2 bg-primary text-white p-12 relative overflow-hidden">
        {/* Was a hotlinked Unsplash photograph: an uncredited third-party
            asset fetched on every render. Replaced with an owned gradient
            until licensed photography exists (see brandbook, open items). */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-secondary opacity-90"></div>
        <div className="relative z-10 text-center">
          <h1 className="text-5xl font-bold tracking-wider mb-2">DS Airlines</h1>
          <p className="text-sm font-light tracking-[0.3em] uppercase opacity-80">Delos Skyways</p>
          <div className="mt-12 text-left space-y-6">
            <h2 className="text-3xl font-semibold leading-tight">Your journey<br />begins here.</h2>
            <p className="text-sm opacity-80 max-w-sm">Short-haul across Europe from Athens and Thessaloniki. Cabin bag included, in every fare.</p>
          </div>
        </div>
      </div>

      {/* Form Side */}
      <div className="flex items-center justify-center w-full md:w-1/2 p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="text-center md:text-left mb-10">
            <h2 className="text-3xl font-bold text-primary mb-2">Welcome Back</h2>
            <p className="text-gray-500 text-sm">Please sign in to your account</p>
          </div>

          {error && (
            <div className="bg-red-50 border-l-4 border-danger p-4 mb-6">
              <p className="text-danger text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-primary text-sm font-bold mb-2 tracking-wide uppercase">Username</label>
              <input 
                type="text" 
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-colors" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                placeholder="Enter your username"
                required 
              />
            </div>
            <div>
              <div className="flex justify-between mb-2 items-center">
                <label className="block text-primary text-sm font-bold tracking-wide uppercase">Password</label>
                <a href="#" className="text-xs text-secondary hover:underline font-semibold">Forgot Password?</a>
              </div>
              <input 
                type="password" 
                className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-colors" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                placeholder="••••••••"
                required 
              />
            </div>
            <button 
              type="submit" 
              className="w-full bg-primary text-white font-bold py-3 px-4 rounded-lg hover:bg-secondary transition-colors duration-300 shadow-md mt-4"
            >
              Sign In
            </button>
          </form>
          
          <div className="mt-8 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <a href="/register" className="text-secondary font-bold hover:underline transition-all">Sign Up</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
