import axios from 'axios';
import { token } from '../auth/authToken';

export const authService = {
  async login(username: string, password: string): Promise<boolean> {
    try {
      const resp = await axios.post('/auth/login', { username, password });
      if (resp.status === 200) {
        const data = resp.data;
        if (data?.access_token) {
          token.setAccessToken(data.access_token);
          return true;
        }
      }
    } catch (err) {
      console.log(`Backend unavailable or login failed: ${err}`);
    }
    return false;
  },
};
