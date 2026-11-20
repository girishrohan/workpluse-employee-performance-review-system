import { SignJWT, jwtVerify } from 'jose';
import type { SessionPayload } from './types';

const ALGORITHM = 'HS256';
const TOKEN_EXPIRY = '24h';

function getSecretKey(secret: string): Uint8Array {
  return new TextEncoder().encode(secret);
}

export async function createToken(payload: SessionPayload, secret: string): Promise<string> {
  const key = getSecretKey(secret);
  const token = await new SignJWT({ ...payload })
    .setProtectedHeader({ alg: ALGORITHM })
    .setIssuedAt()
    .setExpirationTime(TOKEN_EXPIRY)
    .sign(key);
  return token;
}

export async function verifyToken(token: string, secret: string): Promise<SessionPayload | null> {
  try {
    const key = getSecretKey(secret);
    const { payload } = await jwtVerify(token, key, {
      algorithms: [ALGORITHM],
    });
    return payload as unknown as SessionPayload;
  } catch {
    return null;
  }
}

export function extractTokenFromCookie(cookieHeader: string | null): string | null {
  if (!cookieHeader) return null;
  const cookies = cookieHeader.split(';').map(c => c.trim());
  const sessionCookie = cookies.find(c => c.startsWith('workpulse_session='));
  if (!sessionCookie) return null;
  return sessionCookie.split('=')[1];
}