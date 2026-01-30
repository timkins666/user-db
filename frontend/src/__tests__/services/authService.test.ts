import axios from 'axios';

jest.mock('axios');

const mockedAxios = axios as jest.Mocked<any>;

import { authService } from '../../services/authService';
import { token } from '../../auth/authToken';

describe('authService.login', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    token.setAccessToken(null);
  });

  test('returns true and stores access token on 200', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: { access_token: 'fake-token' },
    });

    const ok = await authService.login('alice', 'password');

    expect(mockedAxios.post).toHaveBeenCalledWith('/auth/login', {
      username: 'alice',
      password: 'password',
    });
    expect(ok).toBe(true);
    expect(token.getAccessToken()).toBe('fake-token');
  });

  test('returns false when access_token is missing', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 200,
      data: {},
    });

    const ok = await authService.login('alice', 'password');

    expect(ok).toBe(false);
    expect(token.getAccessToken()).toBe(null);
  });

  test('returns false when status is not 200', async () => {
    mockedAxios.post.mockResolvedValueOnce({
      status: 401,
      data: { access_token: 'should-not-be-used' },
    });

    const ok = await authService.login('alice', 'bad');

    expect(ok).toBe(false);
    expect(token.getAccessToken()).toBe(null);
  });

  test('returns false on axios error', async () => {
    mockedAxios.post.mockRejectedValueOnce(new Error('network'));

    const ok = await authService.login('alice', 'password');

    expect(ok).toBe(false);
    expect(token.getAccessToken()).toBe(null);
  });
});
