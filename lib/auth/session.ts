import { getIronSession, IronSession } from 'iron-session';
import { cookies } from 'next/headers';
import type { SessionPayload } from './types';

export interface SessionData {
  user?: SessionPayload;
}

const sessionOptions = {
  password: process.env.AUTH_SECRET!,
  cookieName: 'workpulse_session',
  cookieOptions: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 60 * 60 * 24, // 24 hours
    sameSite: 'lax' as const,
    path: '/',
  },
};

async function getSessionInstance(): Promise<IronSession<SessionData>> {
  const cookieStore = await cookies();
  return getIronSession<SessionData>(cookieStore, sessionOptions);
}

export async function getSession(): Promise<SessionPayload | null> {
  const session = await getSessionInstance();
  return session.user ?? null;
}

export async function setSession(payload: SessionPayload): Promise<void> {
  const session = await getSessionInstance();
  session.user = payload;
  await session.save();
}

export async function clearSession(): Promise<void> {
  const session = await getSessionInstance();
  session.destroy();
}

export async function updateSession(payload: Partial<SessionPayload>): Promise<void> {
  const session = await getSessionInstance();
  if (session.user) {
    session.user = { ...session.user, ...payload };
    await session.save();
  }
}