import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";

// Panel/portal ana giriş noktaları: oturum yoksa doğrudan Clerk'in giriş
// ekranına değil, önce landing page'e ("/") düşsün — kullanıcı orada ürünü
// görüp bilinçli olarak "Giriş Yap"a tıklasın.
const isLandingGatedRoute = createRouteMatcher(["/dashboard(.*)", "/portal", "/portal/tickets(.*)"]);
// Bağlam taşıyan linkler (davet, şirkete özel yeni talep linki): bunlara
// tıklayan kişi zaten nereye gideceğini biliyor, landing page'e uğratmadan
// doğrudan giriş ekranına gidip işlem sonrası aynı linke geri dönmeli.
const isDirectSignInRoute = createRouteMatcher(["/invite(.*)", "/portal/new(.*)"]);

export default clerkMiddleware(async (auth, req) => {
  if (isLandingGatedRoute(req)) {
    await auth.protect({ unauthenticatedUrl: new URL("/", req.url).toString() });
  } else if (isDirectSignInRoute(req)) {
    await auth.protect();
  }
});

export const config = {
  matcher: ["/((?!_next|.*\\..*).*)", "/(api|trpc)(.*)"],
};
