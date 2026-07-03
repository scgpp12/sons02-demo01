import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

import { clearToken, getToken, setToken } from "@/api/client";
import { fetchMe, login as loginApi } from "@/api/endpoints";
import { oktaAuth } from "@/lib/okta";
import type { CurrentUser } from "@/types";

interface AuthContextValue {
  user: CurrentUser | null;
  loading: boolean;
  /** Okta モードでは引数不要（リダイレクトする）。従来モードでは email/password 必須。 */
  login: (email?: string, password?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      // ---- Okta モード ----
      if (oktaAuth) {
        try {
          // Okta からのリダイレクト戻り（/login/callback）ならトークンを回収
          if (oktaAuth.isLoginRedirect()) {
            const { tokens } = await oktaAuth.token.parseFromUrl();
            oktaAuth.tokenManager.setTokens(tokens);
            window.history.replaceState({}, "", "/");
          }
          const at = (await oktaAuth.tokenManager.get("accessToken")) as
            | { accessToken?: string }
            | undefined;
          if (at?.accessToken) {
            setToken(at.accessToken); // axios の Authorization に載る
            const me = await fetchMe();
            setUser(me);
          }
          // サイレント更新されたら axios 側のトークンも差し替える
          oktaAuth.tokenManager.on("renewed", (key: string, newToken: unknown) => {
            const t = newToken as { accessToken?: string };
            if (key === "accessToken" && t?.accessToken) setToken(t.accessToken);
          });
          oktaAuth.start();
        } catch {
          clearToken();
        } finally {
          setLoading(false);
        }
        return;
      }

      // ---- 従来モード（アプリ内蔵JWT）----
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }
      fetchMe()
        .then((u) => setUser(u))
        .catch(() => clearToken())
        .finally(() => setLoading(false));
    };
    void init();
  }, []);

  const login = async (email?: string, password?: string) => {
    if (oktaAuth) {
      await oktaAuth.signInWithRedirect(); // Okta のログイン画面へ
      return;
    }
    const token = await loginApi(email ?? "", password ?? "");
    setToken(token.access_token);
    const me = await fetchMe();
    setUser(me);
  };

  const logout = () => {
    clearToken();
    setUser(null);
    if (oktaAuth) {
      oktaAuth.tokenManager.clear();
      void oktaAuth.signOut({ postLogoutRedirectUri: window.location.origin });
      return;
    }
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
