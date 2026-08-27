import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { SITE_DESCRIPTION, SITE_TITLE } from '../consts';
import { getPublishedPosts } from '../utils/posts';

/*
 * /rss.xml 엔드포인트.
 *
 * 페이지가 아니라 엔드포인트이므로 GET을 export한다.
 * 목록은 홈·태그 페이지와 같은 getPublishedPosts를 쓴다 —
 * draft 판정과 정렬 규칙이 갈리지 않게 하려는 것.
 *
 * 화면에는 RSS 링크를 노출하지 않지만 피드 자체는 만든다.
 * 발견은 BaseLayout의 <link rel="alternate">가 담당한다.
 */
export async function GET(context: APIContext) {
  const posts = await getPublishedPosts();

  return rss({
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    // astro.config.mjs의 site 값. 여기서 각 글의 절대 URL이 만들어진다.
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title,
      description: post.data.description,
      pubDate: post.data.pubDate,
      link: `/posts/${post.id}/`,
      // RSS의 category. 리더에서 주제 분류로 쓰인다.
      categories: post.data.tags,
    })),
    customData: '<language>ko</language>',
  });
}
