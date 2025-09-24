import dayjs from 'dayjs';
import type { NewUser, User } from '../types/user';

const API_BASE = 'http://localhost:8000';

export const userService = {
  async getUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE}/users`);
    const users: User[] = await response.json();
    return users.map((user: User) => ({
      ...user,
      dateOfBirth: dayjs(user.dateOfBirth),
      age: dayjs().diff(user.dateOfBirth, 'day'),
    }));
  },

  async createUser(userData: NewUser): Promise<User | null> {
    const response = await fetch(`${API_BASE}/users/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user: {
          ...userData,
          dateOfBirth: userData.dateOfBirth?.format('YYYY-MM-DD'),
        },
      }),
    });

    if (!response.ok) {
      return null;
    }

    const newUser: User = await response.json();
    return {
      ...newUser,
      dateOfBirth: dayjs(newUser.dateOfBirth),
      age: dayjs().diff(userData.dateOfBirth, 'day'),
    };
  },

  async deleteUser(id: string): Promise<void> {
    await fetch(`${API_BASE}/user/${id}`, { method: 'DELETE' });
  },
};
