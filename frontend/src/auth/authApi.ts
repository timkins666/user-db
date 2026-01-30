import axios from "axios";
import { token } from "./authToken";
import { API_URL } from "../config/constants";

export async function refreshAccessToken(): Promise<string> {
  const res = await axios.post(
    `/auth/refresh`,
    {},
    {
      withCredentials: true, // send refresh cookie
    },
  );

  const newToken = res.data.access_token as string;

  token.setAccessToken(newToken);

  return newToken;
}
