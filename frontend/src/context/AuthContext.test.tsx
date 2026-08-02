import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import api from '../api';
import { AuthProvider, useAuth } from './AuthContext';

vi.mock('../api', () => ({
  default: { get: vi.fn() },
}));

const PROFILE = {
  id: 'c0ffee00-0000-4000-8000-000000000001',
  email: 'ada@example.com',
  username: 'ada',
  full_name: 'Ada Papadopoulou',
  passport_number: 'AB123456',
  is_admin: false,
  is_active: true,
};

const Probe = () => {
  const { user, loading, login, logout } = useAuth();
  if (loading) return <span>loading</span>;
  return (
    <>
      <span data-testid="user">{user ? user.full_name : 'anonymous'}</span>
      <button onClick={() => login('a-new-token')}>login</button>
      <button onClick={logout}>logout</button>
    </>
  );
};

const renderProbe = () =>
  render(
    <AuthProvider>
      <Probe />
    </AuthProvider>,
  );

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockReset();
  });

  it('does not call the API when there is no token', async () => {
    renderProbe();
    await screen.findByTestId('user');
    expect(api.get).not.toHaveBeenCalled();
    expect(screen.getByTestId('user')).toHaveTextContent('anonymous');
  });

  it('fetches the real profile from the server, not the token', async () => {
    // The previous implementation decoded the JWT and filled the rest with
    // placeholders, so every session displayed the literal name "User"
    // (DEF-016). There is no name in the token to decode.
    localStorage.setItem('token', 'a.b.c');
    vi.mocked(api.get).mockResolvedValue({ data: PROFILE });

    renderProbe();

    expect(await screen.findByTestId('user')).toHaveTextContent('Ada Papadopoulou');
    expect(api.get).toHaveBeenCalledWith('/auth/me');
  });

  it('discards a token the server rejects', async () => {
    localStorage.setItem('token', 'stale.token.value');
    vi.mocked(api.get).mockRejectedValue(new Error('401'));

    renderProbe();

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('anonymous'));
    // A token the server has rejected must not keep looking like a session.
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('stores the token and loads the profile on login', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: PROFILE });
    renderProbe();
    await screen.findByTestId('user');

    await userEvent.click(screen.getByRole('button', { name: 'login' }));

    await waitFor(() =>
      expect(screen.getByTestId('user')).toHaveTextContent('Ada Papadopoulou'),
    );
    expect(localStorage.getItem('token')).toBe('a-new-token');
  });

  it('clears both the token and the profile on logout', async () => {
    localStorage.setItem('token', 'a.b.c');
    vi.mocked(api.get).mockResolvedValue({ data: PROFILE });
    renderProbe();
    await screen.findByTestId('user');

    await userEvent.click(screen.getByRole('button', { name: 'logout' }));

    expect(screen.getByTestId('user')).toHaveTextContent('anonymous');
    expect(localStorage.getItem('token')).toBeNull();
  });

  it('throws when used outside the provider', () => {
    const quiet = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<Probe />)).toThrow(/must be used within an AuthProvider/);
    quiet.mockRestore();
  });
});
