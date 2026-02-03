import MockDate from 'mockdate';
import dayjs from 'dayjs';
import { vi } from 'vitest';
import type { NewUser } from '../../types/user';

const apiInstance = vi.hoisted(() => ({
  get: vi.fn(),
  post: vi.fn(),
  delete: vi.fn(),
  interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
}));

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => apiInstance),
  },
}));

import { userService } from '../../services/userService';

describe('userService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

    apiInstance.get.mockResolvedValueOnce({ data: mockUsers });

    const result = await userService.getUsers();

    expect(apiInstance.get).toHaveBeenCalledWith('/users');
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
    apiInstance.post.mockResolvedValueOnce({ data: mockResponse });

    const result = await userService.createUser(userData);

    expect(apiInstance.post).toHaveBeenCalledWith('/users/create', {
      user: { ...userData, dateOfBirth: '1990-01-01' },
    });
    expect(result).toEqual({ ...mockResponse, age: 365 });
  });

  test('createUser returns null for failed request', async () => {
    const userData: NewUser = {
      firstname: 'John',
      lastname: 'Doe',
      dateOfBirth: dayjs('1990-01-01'),
    };
    apiInstance.post.mockRejectedValueOnce(new Error('failed'));

    const result = await userService.createUser(userData);

    expect(result).toBe(null);
  });

  test('deleteUser sends DELETE request', async () => {
    apiInstance.delete.mockResolvedValueOnce({});

    await userService.deleteUser('1');

    expect(apiInstance.delete).toHaveBeenCalledWith('/user/1');
  });
});
