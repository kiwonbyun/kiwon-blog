import { OGImageRoute } from 'astro-og-canvas';
import { SITE_DESCRIPTION, SITE_TITLE } from '../../consts';
import { getPublishedPosts } from '../../utils/posts';

/*
 * 공유 카드 이미지를 빌드 타임에 그린다.
 *
 * 글의 cover를 쓰지 않고 카드를 직접 그리는 이유 —
 * cover는 목록 썸네일 용도로 고른 이미지라 OG 규격(1200x630, 1.91:1)과
 * 맞지 않는 경우가 많다. 세로로 긴 다이어그램은 중앙만 잘려 의미를 잃고,
 * 작은 스크린샷은 카드에서 뭉개진다. 게다가 이미지가 없는 글은 카드가 빈다.
 *
 * 제목을 크게 그린 카드는 링크만 봐도 무슨 글인지 알 수 있고 모든 글이
 * 같은 규격을 갖는다. cover는 목록 썸네일이라는 원래 역할로 남는다.
 */

const posts = await getPublishedPosts();

/** 경로(키)가 그대로 /og/<키>.png 가 된다. */
const pages: Record<string, { title: string; description: string }> = {
  home: { title: SITE_TITLE, description: SITE_DESCRIPTION },
  about: { title: 'About', description: '이 블로그와 글쓴이에 대해' },
};

for (const post of posts) {
  pages[`posts/${post.id}`] = {
    title: post.data.title,
    description: post.data.description,
  };
}

/*
 * 한글을 그리려면 폰트 파일을 직접 넘겨야 한다. woff2는 canvaskit이 읽지
 * 못하므로 pretendard 패키지가 함께 제공하는 otf를 쓴다.
 * (이미 devDependency로 있는 패키지라 새로 받을 것이 없다)
 */
const FONT_DIR = './node_modules/pretendard/dist/public/static';

export const { getStaticPaths, GET } = await OGImageRoute({
  param: 'route',
  pages,
  getImageOptions: (_path, page: { title: string; description: string }) => ({
    title: page.title,
    description: page.description,

    // 사이트의 종이색 배경. 카드가 어느 앱에 놓여도 사이트와 같은 인상을 준다.
    bgGradient: [[253, 252, 250]],

    // 좌측 굵은 선 — 에디토리얼 판면의 규칙선을 카드로 옮긴 것.
    border: { color: [28, 25, 23], width: 24, side: 'inline-start' },
    padding: 72,

    fonts: [`${FONT_DIR}/Pretendard-Bold.otf`, `${FONT_DIR}/Pretendard-Regular.otf`],
    font: {
      title: {
        color: [28, 25, 23],
        size: 64,
        weight: 'Bold',
        lineHeight: 1.3,
        families: ['Pretendard'],
      },
      description: {
        color: [107, 101, 96],
        size: 30,
        weight: 'Normal',
        lineHeight: 1.5,
        families: ['Pretendard'],
      },
    },

    cacheDir: './node_modules/.astro-og-canvas',
  }),
});
