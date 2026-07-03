// Okta 認証クライアント（PKCE）。
// VITE_OKTA_ISSUER / VITE_OKTA_CLIENT_ID が未設定なら null = 従来のID/PWログインにフォールバック。
import { OktaAuth } from "@okta/okta-auth-js";

const issuer = import.meta.env.VITE_OKTA_ISSUER;
const clientId = import.meta.env.VITE_OKTA_CLIENT_ID;

export const oktaAuth =
  issuer && clientId
    ? new OktaAuth({
        issuer,
        clientId,
        redirectUri: `${window.location.origin}/login/callback`,
        // offline_access = リフレッシュトークン（サイレント更新用）
        scopes: ["openid", "profile", "email", "offline_access"],
        pkce: true,
      })
    : null;
