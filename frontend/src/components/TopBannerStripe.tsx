import { useEffect, useMemo, useState } from "react";
import { AppBar, Box, Toolbar, Typography } from "@mui/material";
import { Person } from "@mui/icons-material";
import { token, registerAccessTokenListener } from "../auth/authToken";
import { parseJwtPayload } from "../auth/jwt";

function getUsernameFromToken(accessToken: string | null): string | null {
  if (!accessToken) {
    return null;
  }
  const payload = parseJwtPayload(accessToken);
  const subject = payload?.sub;
  return typeof subject === "string" && subject.trim() ? subject : null;
}

export default function TopBannerStripe({
  children,
}: {
  children: React.ReactNode;
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
    () => (username ? username.toLowerCase() : ""),
    [username],
  );

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar position="static" elevation={0} sx={{ bgcolor: "primary.main" }}>
        <Toolbar
          sx={{
            minHeight: 44,
            display: "flex",
            justifyContent: "flex-end",
            gap: 1,
          }}
        >
          <Person fontSize="small" />
          <Typography
            variant="body2"
            sx={{ fontFamily: "monospace" }}
            data-testid="top-banner-username"
          >
            {usernameLower}
          </Typography>
        </Toolbar>
      </AppBar>

      <Box>{children}</Box>
    </Box>
  );
}
