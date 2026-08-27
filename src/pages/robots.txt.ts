import type { APIContext } from 'astro';

/*
 * public/robots.txt로 두지 않고 엔드포인트로 만드는 이유.
 *
 * sitemap 주소는 절대 URL이어야 해서 도메인을 적어야 하는데,
 * public/의 정적 파일에는 변수를 쓸 수 없어 도메인이 하드코딩된다.
 * 엔드포인트로 만들면 astro.config.mjs의 site(=consts.ts의 SITE_URL)를
 * 그대로 쓰므로, 도메인이 확정될 때 consts.ts 한 줄만 고치면 된다.
 */
export function GET(context: APIContext) {
  const sitemapURL = new URL('sitemap-index.xml', context.site);

  const body = [
    'User-agent: *',
    'Allow: /',
    '',
    `Sitemap: ${sitemapURL.href}`,
    '',
  ].join('\n');

  return new Response(body, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
