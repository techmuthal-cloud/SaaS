# Authentication and Authorization

## 1. Recommended approach

Use one managed identity provider for the MVP (choose Supabase Auth or Clerk after reviewing pricing, deployment and team familiarity). Do not implement a custom password system unless there is a compelling requirement.

The identity provider authenticates the human. SellerFlow's database authorizes that person against workspace memberships and roles.

## 2. Sign-in methods

MVP:
- Email/password or passwordless email flow supported by chosen provider.
- Email verification.
- Password reset if password login is enabled.

Later:
- Google sign-in if customer research supports it.
- MFA for privileged roles.
- Enterprise SSO if required by larger customers.

Avoid collecting phone numbers or adding OTP flows without a product need and operational plan.

## 3. Token handling

- Verify token signature, issuer, audience, expiry and intended claims on the API.
- Use short-lived access tokens and provider-supported refresh flow.
- Prefer secure, HttpOnly, SameSite cookies for browser sessions when architecture permits.
- Never store long-lived provider secrets in local storage.
- Do not trust workspace ID or role sent by the browser; load membership from the backend database.
- Rotate provider keys and revoke sessions on suspected compromise.

## 4. Workspace roles

| Role | Read | Upload/process | Review financial results | Invite/manage members | Billing/security |
|---|---:|---:|---:|---:|---:|
| Viewer | Yes | No | No | No | No |
| Analyst | Yes | Yes | Yes | No | No |
| Accountant | Assigned scope | If granted | Yes | No | No |
| Admin | Yes | Yes | Yes | Yes | Limited |
| Owner | Yes | Yes | Yes | Yes | Yes |

Role definitions must be enforced server-side and may be refined during implementation.

## 5. Invitation workflow

1. Owner/admin enters invitee email and role.
2. API verifies inviter permission and workspace limits.
3. Invitation record is created with a random, hashed, single-use token and expiry.
4. Email is sent through an approved provider.
5. Invitee authenticates and accepts.
6. API checks token, expiry and email identity before creating membership.
7. Audit event is written.

## 6. Account lifecycle

- Verify email before granting access to sensitive workflows.
- Support session logout and revoke.
- Provide account export/deletion request path.
- Prevent deletion of the last owner without transfer or workspace closure.
- Revoke workspace membership immediately when removed.
- Keep audit records according to documented retention and legal requirements.

## 7. Security checks

- Rate-limit login, password reset and invitation endpoints.
- Use MFA for privileged access when available.
- Alert on unusual privilege changes.
- Do not reveal whether an email is registered in password-reset responses.
- Test expired, revoked, malformed and wrong-audience tokens.
