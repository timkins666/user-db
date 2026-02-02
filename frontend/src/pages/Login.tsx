import { useState } from 'react';
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
} from '@mui/material';
import { authService } from '../services/authService';

export default function Login({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e?: React.SyntheticEvent<HTMLFormElement>) => {
    e?.preventDefault();
    setError(null);
    setLoading(true);

    if (!username || !password) {
      setError('Enter username and password');
      setLoading(false);
      return;
    }

    try {
      const ok = await authService.login(username, password);
      if (ok) {
        onLogin();
      } else {
        setError('Invalid credentials');
      }
    } catch (err) {
      setError('Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="xs" sx={{ mt: 8 }}>
      <Box component="form" onSubmit={handleSubmit}>
        <Typography variant="h5" sx={{ mb: 2 }}>
          Sign in
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          label="username"
          type="text"
          fullWidth
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          sx={{ mb: 2 }}
        />

        <TextField
          label="password"
          type="password"
          fullWidth
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          sx={{ mb: 2 }}
        />

        <Button variant="contained" fullWidth type="submit" disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </Button>
      </Box>
    </Container>
  );
}
