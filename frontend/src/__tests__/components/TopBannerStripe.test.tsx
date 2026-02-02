import { render, screen } from "@testing-library/react";
import TopBannerStripe from "../../components/TopBannerStripe";
import { token } from "../../auth/authToken";

function makeFakeJwt(payload: object): string {
  const header = { alg: "none", typ: "JWT" };
  const b64url = (obj: object) =>
    Buffer.from(JSON.stringify(obj))
      .toString("base64")
      .replace(/=/g, "")
      .replace(/\+/g, "-")
      .replace(/\//g, "_");

  return `${b64url(header)}.${b64url(payload)}.`;
}

describe("TopBannerStripe", () => {
  beforeEach(() => {
    token.setAccessToken(null);
  });

  test("shows lowercased username from JWT sub", () => {
    token.setAccessToken(makeFakeJwt({ sub: "ALIce" }));

    render(
      <TopBannerStripe>
        <div>content</div>
      </TopBannerStripe>,
    );

    expect(screen.getByText("content")).toBeInTheDocument();
    expect(screen.getByTestId("top-banner-username")).toHaveTextContent(
      "alice",
    );
  });
});
