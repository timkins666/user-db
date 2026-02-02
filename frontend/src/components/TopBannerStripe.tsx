import { useEffect, useMemo, useState } from 'react';
import {
  AppBar,
  Box,
  IconButton,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import { Logout, Person } from '@mui/icons-material';
import { token, registerAccessTokenListener } from '../auth/authToken';
import { parseJwtPayload } from '../auth/jwt';

function getUsernameFromToken(accessToken: string | null): string | null {
  if (!accessToken) {
    return null;
  }
  const payload = parseJwtPayload(accessToken);
  const subject = payload?.sub;
  return typeof subject === 'string' && subject.trim() ? subject : null;
}

export default function TopBannerStripe({
  children,
  onLogout,
}: {
  children: React.ReactNode;
  onLogout?: () => void;
}) {
  const [username, setUsername] = useState<string | null>(() =>
    getUsernameFromToken(token.getAccessToken()),
  );

  useEffect(() => {
    const unsubscribe = registerAccessTokenListener((t) => {
      setUsername(getUsernameFromToken(t));
    });
    return unsubscribe;
  }, []);

  const usernameLower = useMemo(
    () => (username ? username.toLowerCase() : ''),
    [username],
  );

  const handleLogout = () => {
    token.setAccessToken(null);
    onLogout?.();
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
      }}
    >
      <AppBar position="static" elevation={0}>
        <Toolbar
          variant="dense"
          sx={{
            minHeight: { xs: 40, sm: 40 },
            display: 'flex',
            justifyContent: 'flex-end',
            gap: 1,
            px: 1.5,
            py: 0,
            backdropFilter: 'blur(10px)',
            '& .MuiIconButton-root': {
              p: 0.5,
            },
          }}
        >
          <Person fontSize="small" />
          <Typography
            variant="body2"
            sx={{ fontFamily: 'monospace' }}
            data-testid="top-banner-username"
          >
            {usernameLower}
          </Typography>
          <Tooltip title="Logout">
            <IconButton
              onClick={handleLogout}
              color="inherit"
              size="small"
              aria-label="logout"
              sx={{ ml: 3 }}
            >
              <Logout fontSize="small" />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Box>{children}</Box>
    </Box>
  );
}
