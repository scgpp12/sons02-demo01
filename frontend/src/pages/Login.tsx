import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { errMessage } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/hooks/useAuth";
import { oktaAuth } from "@/lib/okta";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(errMessage(err, "ログインに失敗しました"));
    } finally {
      setLoading(false);
    }
  };

  const onOktaLogin = async () => {
    setError("");
    setLoading(true);
    try {
      await login(); // Okta のログイン画面へリダイレクト
    } catch (err) {
      setError(errMessage(err, "ログインに失敗しました"));
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-center text-lg">SES社内管理システム</CardTitle>
        </CardHeader>
        <CardContent>
          {oktaAuth ? (
            // Okta SSO モード
            <div className="space-y-4">
              <p className="text-center text-sm text-muted-foreground">
                社内アカウント（Okta）でサインインしてください
              </p>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button className="w-full" onClick={onOktaLogin} disabled={loading}>
                {loading ? "リダイレクト中..." : "Okta でサインイン"}
              </Button>
            </div>
          ) : (
            // 従来モード（ローカル開発など Okta 未設定時）
            <form onSubmit={onSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="email">メールアドレス</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="password">パスワード</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "ログイン中..." : "ログイン"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
