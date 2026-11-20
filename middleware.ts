import { NextResponse, type NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

const AUTH_SECRET = process.env.AUTH_SECRET;
const ALGORITHM = 'HS256';

const protectedPaths = ['/dashboard', '/employees', '/cycles', '/assessments', '/settings'];
const authPaths = ['/auth/login', '/auth/sign-up'];

function getSecretKey(): Uint8Array {
  return new TextEncoder().encode(AUTH_SECRET!);
}

function extractTokenFromCookie(cookieHeader: string | null): string | null {
  if (!cookieHeader) return null;
  const cookies = cookieHeader.split(';').map(c => c.trim());
  const sessionCookie = cookies.find(c => c.startsWith('workpulse_session='));
  if (!sessionCookie) return null;
  return sessionCookie.split('=')[1];
}

async function verifySession(request: NextRequest): Promise<{ userId: string; email: string; role: string } | null> {
  if (!AUTH_SECRET) return null;
  
  const token = extractTokenFromCookie(request.headers.get('cookie'));
  if (!token) return null;

  try {
    const { payload } = await jwtVerify(token, getSecretKey(), {
      algorithms: [ALGORITHM],
    });
    return {
      userId: payload.userId as string,
      email: payload.email as string,
      role: payload.role as string,
    };
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  // Skip if AUTH_SECRET not configured
  if (!AUTH_SECRET) {
    return NextResponse.next();
  }

  const user = await verifySession(request);
  const pathname = request.nextUrl.pathname;

  // Protected routes - redirect to login if not authenticated
  const isProtectedPath = protectedPaths.some((path) => pathname.startsWith(path));
  if (isProtectedPath && !user) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = '/auth/login';
    redirectUrl.searchParams.set('next', pathname);
    return NextResponse.redirect(redirectUrl);
  }

  // Auth routes - redirect to dashboard if already authenticated
  const isAuthPath = authPaths.some((path) => pathname.startsWith(path));
  if (isAuthPath && user) {
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = '/dashboard';
    return NextResponse.redirect(redirectUrl);
  }

  // Add user info to request headers for Server Components
  const response = NextResponse.next();
  if (user) {
    response.headers.set('x-user-id', user.userId);
    response.headers.set('x-user-email', user.email);
    response.headers.set('x-user-role', user.role);
  }

  return response;
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     * - api routes (handled separately)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$|public|api).*)',
  ],
}