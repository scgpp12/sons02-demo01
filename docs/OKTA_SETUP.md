# Okta 开发者账号注册 & SPA 应用登记手顺

> 目的：给 demo 环境接入真实的 Okta PKCE 认证（B案完整形）。
> 只有「注册账号」必须本人操作，做完把 3 个值发给 Claude 即可，后续接线（前端改造+API GW authorizer）由 Claude 完成。

## Step 1. 注册 Okta 开发者账号（免费）

1. 打开 https://developer.okta.com/signup/
2. 选择免费的开发者/Integrator 计划，用邮箱注册（也可 Google/GitHub 登录）
3. 收到激活邮件 → 设置密码 + MFA（Okta Verify 手机 App 或短信）
4. 登录后你会得到一个专属域名，形如：`dev-12345678.okta.com`
   （管理画面右上角头像下能看到，**记下它 = 值A**）

## Step 2. 创建 SPA 应用（OIDC + PKCE）

1. 左侧菜单 **Applications → Applications → Create App Integration**
2. 选择：
   - Sign-in method: **OIDC - OpenID Connect**
   - Application type: **Single-Page Application**
3. 设置画面：
   - App integration name: `sons02-demo01`
   - Grant type: **Authorization Code** 勾选（PKCE 对 SPA 自动强制，无需 client secret）
   - **Sign-in redirect URIs**:
     - `https://d1cnlo8n0t8l8j.cloudfront.net/login/callback`
     - `http://localhost:5173/login/callback` （本地开发用）
   - **Sign-out redirect URIs**:
     - `https://d1cnlo8n0t8l8j.cloudfront.net`
     - `http://localhost:5173`
   - Assignments: 先选 **Allow everyone in your organization to access**（个人环境只有你一人）
4. Save 后记下 **Client ID**（形如 `0oa...`，**= 值B**）

## Step 3. 信任来源（CORS/Trusted Origins）

1. **Security → API → Trusted Origins → Add Origin**
2. 添加：
   - Origin: `https://d1cnlo8n0t8l8j.cloudfront.net`，勾选 CORS + Redirect
   - Origin: `http://localhost:5173`，勾选 CORS + Redirect

## Step 4. 确认授权服务器（Issuer）

1. **Security → API → Authorization Servers**
2. 如果列表里有 **default**：
   - Issuer 形如 `https://dev-12345678.okta.com/oauth2/default`（**= 值C**）
   - Audience 默认 `api://default`
3. ⚠️ 如果你的免费计划**没有** default 授权服务器（新 Integrator 计划可能砍掉了）：
   - 不用慌，改用 **ID Token 方案**：Issuer = `https://dev-12345678.okta.com`（org 本体），Audience = Client ID（值B）
   - 把「没有 default」这个情况一并告诉 Claude 即可，接线方式会相应调整

## Step 5. 把 3 个值发给 Claude

```
值A: Okta domain     = dev-XXXXXXXX.okta.com
值B: Client ID       = 0oaXXXXXXXXXXXX
值C: Issuer          = https://dev-XXXXXXXX.okta.com/oauth2/default （或无default时说明）
```

之后 Claude 会：
1. 前端接入 `@okta/okta-auth-js`（PKCE 登录、token 自动续期、登出）
2. API Gateway 挂 **JWT authorizer**（issuer/audience 验签，验票在网关层完成）
3. 后端读取网关传递的用户 claim（email）→ 映射到应用内用户/角色（RBAC 保持）
