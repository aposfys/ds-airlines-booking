import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import ThemeToggle from '../components/ThemeToggle';

// Field names match the API payload exactly.
const FIELDS = [
  { name: 'full_name', label: 'Full name', type: 'text', autoComplete: 'name' },
  { name: 'username', label: 'Username', type: 'text', autoComplete: 'username' },
  { name: 'email', label: 'Email address', type: 'email', autoComplete: 'email' },
  { name: 'passport_number', label: 'Passport number', type: 'text', autoComplete: 'off' },
  { name: 'password', label: 'Password', type: 'password', autoComplete: 'new-password' },
] as const;

type FormState = Record<(typeof FIELDS)[number]['name'], string>;

const Register = () => {
  const [formData, setFormData] = useState<FormState>({
    full_name: '',
    username: '',
    email: '',
    passport_number: '',
    password: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/auth/register', formData);
      navigate('/login');
    } catch (err) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data
        ?.detail;
      setError(
        typeof detail === 'string'
          ? detail
          : 'We could not create your account. Check your details and try again.',
      );
    }
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen">
      <div className="af-grain hidden md:flex flex-col justify-between w-1/2 p-12 bg-sunken border-r border-hairline order-last md:order-first">
        <span className="af-eyebrow">DS Airlines</span>
        <div>
          {/* Star Alliance and Miles+Bonus were removed here: a real alliance
              DS does not belong to, and Aegean's registered programme. */}
          <h1 className="af-hero" style={{ fontSize: 'var(--display-3)' }}>
            Join<br />Meltemi Club
          </h1>
          <p className="af-prose mt-6 text-muted">
            Collect points on every DS flight and spend them on fares, seats and bags.
            Free to join.
          </p>
        </div>
        <span className="af-label text-faint">220 seats · one fleet · seven routes</span>
      </div>

      <div className="flex items-center justify-center w-full md:w-1/2 p-6 md:p-12">
        <div className="w-full max-w-md">
          <div className="flex justify-end mb-4">
            <ThemeToggle />
          </div>
          <span className="af-eyebrow md:hidden">DS Airlines</span>
          <h2 className="text-xl md:text-2xl uppercase tracking-[-0.028em] mt-2 md:mt-0">
            Create account
          </h2>
          <p className="text-muted text-sm mt-2 mb-8">
            Register to start booking flights.
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
            {FIELDS.map((field) => (
              <div key={field.name}>
                <label className="af-label block mb-2 text-muted" htmlFor={field.name}>
                  {field.label}
                </label>
                <input
                  id={field.name}
                  type={field.type}
                  autoComplete={field.autoComplete}
                  className="ds-field"
                  value={formData[field.name]}
                  onChange={(e) =>
                    setFormData({ ...formData, [field.name]: e.target.value })
                  }
                  required
                />
                {field.name === 'password' && (
                  <p className="text-2xs text-faint mt-2">
                    At least 8 characters, including a letter and a digit.
                  </p>
                )}
              </div>
            ))}

            <button type="submit" className="ds-action ds-action--primary w-full">
              Create account
            </button>
          </form>

          <p className="text-sm text-muted mt-8 pt-6 border-t border-hairline">
            Already registered?{' '}
            <a href="/login" className="text-editorial">
              Log in
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
