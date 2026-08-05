import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import ThemeToggle from '../components/ThemeToggle';
import { useAuth } from '../context/AuthContext';

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
      // Awaited: login fetches the profile from /auth/me, and navigating
      // before it resolves lands on the dashboard with a null user.
      await login(response.data.access_token);
      navigate('/dashboard');
    } catch {
      setError('That username and password do not match. Check both and try again.');
    }
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      {/* Editorial side. Glass over the bloom, per VANE. */}
      <div className="ds-editorial hidden md:flex flex-col justify-between w-1/2 p-12 border-r border-hairline">
        <span className="ds-eyebrow">DS Airlines</span>
        <div>
          <h1 className="ds-hero">
            Your journey<br />begins here
          </h1>
          <p className="mt-6 text-muted text-base">
            Short-haul across Europe from Athens and Thessaloniki. Cabin bag included,
            in every fare.
          </p>
        </div>
        <span className="ds-label text-muted">ATH · SKG · LHR · CDG · FRA · MUC · FCO · BCN</span>
      </div>

      {/* Form side */}
      <div className="flex items-center justify-center w-full md:w-1/2 p-6 md:p-12">
        <div className="w-full max-w-md">
          <div className="flex justify-end mb-4">
            <ThemeToggle />
          </div>
          <span className="ds-eyebrow md:hidden">DS Airlines</span>
          <h2 className="text-xl md:text-2xl tracking-[-0.03em] mt-2 md:mt-0 font-semibold">
            Log in
          </h2>
          <p className="text-muted text-sm mt-2 mb-8">
            Sign in to manage your bookings.
          </p>

          {error && (
            <div
              role="alert"
              className="border-l-2 border-critical bg-critical-bg text-critical text-sm p-3 mb-6"
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="ds-label block mb-2 text-muted" htmlFor="username">
                Username
              </label>
              <input
                id="username"
                className="ds-field"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </div>

            <div>
              <label className="ds-label block mb-2 text-muted" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className="ds-field"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            {/* One primary action per view. */}
            <button type="submit" className="ds-action ds-action--primary w-full">
              Sign in
            </button>
          </form>

          <p className="text-sm text-muted mt-8 pt-6 border-t border-hairline">
            No account yet?{' '}
            <a href="/register" className="text-editorial">
              Create one
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
