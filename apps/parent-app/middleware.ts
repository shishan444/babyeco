// @MX:ANCHOR: [Next.js middleware for protected route authentication]
// @MX:REASON: [Centralized route protection for dashboard and authenticated pages]
// @MX:SPEC: [SPEC-FE-AUTH-001 - Route protection with session validation]

import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Routes that require authentication
 */
const PROTECTED_ROUTES = ["/dashboard", "/profile", "/settings"];

/**
 * Routes that should redirect authenticated users
 */
const AUTH_ROUTES = ["/login", "/register", "/forgot-password", "/reset-password"];

/**
 * Check if a path requires authentication
 */
function isProtectedRoute(path: string): boolean {
  return PROTECTED_ROUTES.some((route) => path.startsWith(route));
}

/**
 * Check if a path is for authentication (should redirect if logged in)
 */
function isAuthRoute(path: string): boolean {
  return AUTH_ROUTES.some((route) => path.startsWith(route));
}

/**
 * Get token from request cookies
 */
function getToken(request: NextRequest): string | null {
  const token = request.cookies.get("auth-storage")?.value;
  if (!token) return null;

  try {
    // Parse the JSON stored in the cookie
    const storage = JSON.parse(decodeURIComponent(token));
    return storage.state?.token || null;
  } catch {
    return null;
  }
}

/**
 * Middleware to handle route protection and authentication redirects
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = getToken(request);

  const isAuthenticated = Boolean(token);
  const isProtected = isProtectedRoute(pathname);
  const isAuth = isAuthRoute(pathname);

  // Redirect to login if accessing protected route without authentication
  if (isProtected && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Redirect to dashboard if accessing auth route while authenticated
  if (isAuth && isAuthenticated) {
    const redirectParam = request.nextUrl.searchParams.get("redirect");
    const redirectUrl = redirectParam
      ? new URL(redirectParam, request.url)
      : new URL("/dashboard", request.url);
    return NextResponse.redirect(redirectUrl);
  }

  return NextResponse.next();
}

/**
 * Configure which routes the middleware should run on
 */
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes (handled separately)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, fonts, etc.)
     */
    "/((?!api|_next/static|_next/image|favicon.ico|.*\\..*|_next).*)",
  ],
};
