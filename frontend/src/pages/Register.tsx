import { useState } from 'react';
import api from '../api';
import { useNavigate } from 'react-router-dom';

const Register = () => {
  // Field names match the API payload exactly (Phase 1 renamed fullname ->
  // full_name and passport_num -> passport_number to match the schema).
  const [formData, setFormData] = useState({
    full_name: '',
    username: '',
    email: '',
    password: '',
    passport_number: '',
  });
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

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

  const renderFieldLabel = (key: string) => {
    const labels: Record<string, string> = {
      full_name: 'Full Name',
      username: 'Username',
      email: 'Email Address',
      password: 'Password',
      passport_number: 'Passport Number'
    };
    return labels[key] || key;
  };

  return (
    <div className="flex flex-col md:flex-row min-h-screen bg-accent font-sans">
      {/* Visual Side */}
      <div className="hidden md:flex flex-col justify-center items-center w-1/2 bg-primary text-white p-12 relative overflow-hidden order-last md:order-first">
        {/* "A Star Alliance Member" and "Miles+Bonus" were removed here.
            Star Alliance is a real alliance DS Airlines does not belong to,
            and Miles+Bonus is Aegean Airlines' registered programme. */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary via-primary to-secondary opacity-90"></div>
        <div className="relative z-10 text-center">
          <h1 className="text-5xl font-bold tracking-wider mb-2">DS Airlines</h1>
          <p className="text-sm font-light tracking-[0.3em] uppercase opacity-80">Delos Skyways</p>
          <div className="mt-12 text-left space-y-6">
            <h2 className="text-3xl font-semibold leading-tight">Join Meltemi Club</h2>
            <p className="text-sm opacity-80 max-w-sm">Collect points on every DS flight and spend them on fares, seats and bags. Free to join.</p>
          </div>
        </div>
      </div>

      {/* Form Side */}
      <div className="flex items-center justify-center w-full md:w-1/2 p-8 bg-white">
        <div className="w-full max-w-md">
          <div className="text-center md:text-left mb-10">
            <h2 className="text-3xl font-bold text-primary mb-2">Create Account</h2>
            <p className="text-gray-500 text-sm">Register to start booking your flights</p>
          </div>

          {error && (
            <div className="bg-red-50 border-l-4 border-danger p-4 mb-6">
              <p className="text-danger text-sm font-medium">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {(Object.keys(formData) as Array<keyof typeof formData>).map((key) => (
              <div key={key}>
                <label className="block text-primary text-xs font-bold tracking-wide uppercase mb-1">
                  {renderFieldLabel(key)}
                </label>
                <input 
                  type={key === 'password' ? 'password' : key === 'email' ? 'email' : 'text'} 
                  name={key}
                  value={formData[key]}
                  onChange={handleChange}
                  placeholder={`Enter your ${renderFieldLabel(key).toLowerCase()}`}
                  className="w-full px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg focus:outline-none focus:border-secondary focus:ring-1 focus:ring-secondary transition-colors" 
                  required 
                />
              </div>
            ))}
            
            <button 
              type="submit" 
              className="w-full bg-secondary text-white font-bold py-3 px-4 rounded-lg hover:bg-primary transition-colors duration-300 shadow-md mt-6"
            >
              Sign Up
            </button>
          </form>
          
          <div className="mt-8 pt-6 border-t border-gray-100 text-center">
            <p className="text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="text-secondary font-bold hover:underline transition-all">Log In</a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
