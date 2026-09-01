import type { APIRoute } from 'astro';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import sharp from 'sharp';
import { getPublishedPosts } from '../../utils/posts';

/*
 * 공유 카드 이미지를 빌드 타임에 만든다.
 *
 * 하는 일은 하나뿐이다 — 글의 대표 이미지를 1200x630(1.91:1)으로 잘라 JPEG로
 * 내보낸다. 제목·설명을 이미지에 그리지 않는 이유는 og:title·og:description이
 * 이미 메타 태그로 나가고, 공유 카드를 그리는 쪽(슬랙·카톡·X 등)이 그 텍스트를
 * 이미지 옆에 붙여주기 때문이다. 이미지에까지 그리면 같은 문장이 두 번 보인다.
 *
 * Astro의 getImage()를 쓰지 않는 이유 — 이미지 서비스가 원본보다 크게 확대하지
 * 않아서, 498x193 같은 작은 커버는 1200x630을 채우지 못하고 그대로 나온다
 * (OG 최소 규격 600x315에도 못 미친다). sharp는 확대해준다.
 *
 * JPEG인 이유 — 커버는 전부 WebP인데 og:image의 WebP 지원은 플랫폼마다 다르다.
 * 특히 카카오톡·페이스북 계열은 JPEG/PNG라야 확실하다.
 */

const POSTS_DIR = './src/content/posts';
/** 커버가 없는 글·페이지가 쓸 기본 이미지. 목록 카드와 같은 것. */
const DEFAULT_COVER = './src/assets/default-cover.webp';

/*
 * 커버 이미지의 파일 경로.
 *
 * frontmatter의 cover는 스키마의 image()를 거치며 ImageMetadata로 바뀌어 있고,
 * 거기에는 src(빌드 산출물 주소)와 크기뿐이라 원본 경로가 없다.
 * 그래서 마크다운의 cover 줄을 직접 읽는다.
 */
function coverPath(id: string): string {
  const md = readFileSync(path.join(POSTS_DIR, `${id}.md`), 'utf-8');
  const found = md.match(/^cover:\s*(\S+)\s*$/m);
  return found ? path.join(POSTS_DIR, found[1].replace(/^\.\//, '')) : DEFAULT_COVER;
}

export async function getStaticPaths() {
  const posts = await getPublishedPosts();

  return [
    { params: { route: 'home.jpg' }, props: { source: DEFAULT_COVER } },
    { params: { route: 'about.jpg' }, props: { source: DEFAULT_COVER } },
    ...posts.map((post) => ({
      params: { route: `posts/${post.id}.jpg` },
      props: { source: coverPath(post.id) },
    })),
  ];
}

export const GET: APIRoute<{ source: string }> = async ({ props }) => {
  const body = await sharp(props.source)
    .resize(1200, 630, {
      fit: 'cover',
      // 'attention' — 잘라낼 때 가장자리가 아니라 눈에 띄는 영역을 남긴다.
      // 커버 비율이 제각각이라(가로로 넓은 것부터 세로로 긴 것까지) 가운데를
      // 기계적으로 자르면 의미 있는 부분이 빠지는 경우가 있다.
      position: 'attention',
    })
    .jpeg({ quality: 82, mozjpeg: true })
    .toBuffer();

  return new Response(body, { headers: { 'Content-Type': 'image/jpeg' } });
};
