import dayjs from 'dayjs';
import { api } from './api';
import type { NewUser, User } from '../types/user';

export const userService = {
  async getUsers(): Promise<User[]> {
    const resp = await api.get('/users');
    const users: User[] = resp.data;
    return users.map((user: User) => ({
      ...user,
      dateOfBirth: dayjs(user.dateOfBirth),
      age: dayjs().diff(user.dateOfBirth, 'day'),
    }));
  },

  async createUser(userData: NewUser): Promise<User | null> {
    try {
      const resp = await api.post('/users/create', {
        user: {
          ...userData,
          dateOfBirth: userData.dateOfBirth?.format('YYYY-MM-DD'),
        },
      });

      const newUser: User = resp.data;
      return {
        ...newUser,
        dateOfBirth: dayjs(newUser.dateOfBirth),
        age: dayjs().diff(userData.dateOfBirth, 'day'),
      };
    } catch (err) {
      return null;
    }
  },

  async deleteUser(id: string): Promise<void> {
    await api.delete(`/user/${id}`);
  },
};
