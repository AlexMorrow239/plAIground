import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Public routes that don't require authentication
  const publicPaths = ["/login", "/", "/_next", "/favicon.ico"];
  
  // Check if the current path is public
  const isPublicPath = publicPaths.some(path => 
    pathname === path || pathname.startsWith("/_next")
  );

  if (isPublicPath) {
    return NextResponse.next();
  }

  // For protected routes, we can't check localStorage in middleware
  // The auth check will be handled client-side by the AuthProvider
  // This is a limitation of Next.js middleware (runs on edge runtime)
  
  // We could check for a cookie if we implement cookie-based auth
  // For now, just allow the request to proceed
  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!api|_next/static|_next/image|favicon.ico|public).*)",
  ],
};