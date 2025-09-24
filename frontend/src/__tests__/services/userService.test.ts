import MockDate from 'mockdate';
import dayjs from 'dayjs';
import { userService } from '../../services/userService';
import type { NewUser } from '../../types/user';

// Mock fetch
global.fetch = jest.fn();

describe('userService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    MockDate.reset();
  });

  test('getUsers fetches users from API', async () => {
    MockDate.set('2022-01-01');

    const mockUsers = [
      {
        id: '1',
        firstname: 'John',
        lastname: 'Doe',
        dateOfBirth: '1990-01-01',
        age: 365.25 * 32,
      },
    ];

    (fetch as jest.Mock).mockResolvedValueOnce({
      json: () => Promise.resolve(mockUsers),
    });

    const result = await userService.getUsers();

    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/users');
    expect(result).toEqual([
      { ...mockUsers[0], dateOfBirth: dayjs('1990-01-01') },
    ]);
  });

  test('createUser posts user data to API', async () => {
    MockDate.set('1991-01-01');

    const userData: NewUser = {
      firstname: 'John',
      lastname: 'Doe',
      dateOfBirth: dayjs('1990-01-01'),
    };
    const mockResponse = { ...userData, id: '1' };
    (fetch as jest.Mock).mockResolvedValueOnce({
      json: () => Promise.resolve(mockResponse),
      ok: true,
    });

    const result = await userService.createUser(userData);

    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/users/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user: {...userData, dateOfBirth: '1990-01-01' }}),
    });
    expect(result).toEqual({...mockResponse, age: 365});
  });

  test('createUser returns null for failed request', async () => {
    const userData: NewUser = {
      firstname: 'John',
      lastname: 'Doe',
      dateOfBirth: dayjs('1990-01-01'),
    };
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
    });

    const result = await userService.createUser(userData);

    expect(result).toBe(null);
  });

  test('deleteUser sends DELETE request', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({});

    await userService.deleteUser('1');

    expect(fetch).toHaveBeenCalledWith('http://localhost:8000/user/1', {
      method: 'DELETE',
    });
  });
});
