import { useState, useEffect } from 'react';
import type { NewUser, User } from '../types/user';
import { userService } from '../services/userService';

export const useUsers = () => {
  const [users, setUsers] = useState<User[]>([]);

  const fetchUsers = async () => {
    try {
      const data = await userService.getUsers();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const createUser = async (userData: NewUser): Promise<boolean> => {
    try {
      const newUser = await userService.createUser(userData);

      if (!newUser) {
        return false;
      }

      setUsers((prevUsers) => [...prevUsers, newUser]);
      return true;
    } catch (error) {
      console.error('Error creating user:', error);
      return false;
    }
  };

  const deleteUser = async (id: string) => {
    try {
      await userService.deleteUser(id);
      setUsers((prevUsers) => prevUsers.filter((user) => user.id !== id));
    } catch (error) {
      console.error('Error deleting user:', error);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  return { users, createUser, deleteUser };
};
