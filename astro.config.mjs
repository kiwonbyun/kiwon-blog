// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';
import { SITE_URL } from './src/consts.ts';

// https://astro.build/config
export default defineConfig({
  // canonical · OG 태그 · RSS · sitemap이 절대 URL을 만들 때 쓴다.
  // 이 값이 없으면 Astro.site가 undefined가 되어 meta 태그가 상대경로로 나간다.
  site: SITE_URL,

  // 빌드 시 dist/sitemap-index.xml과 sitemap-0.xml을 생성한다.
  // 404 페이지는 자동으로 제외된다.
  integrations: [sitemap()],

  markdown: {
    shikiConfig: {
      /*
       * 듀얼 테마. Shiki가 각 토큰에 라이트 색을 인라인 스타일로 넣고
       * 다크 색은 --shiki-dark 커스텀 속성으로 함께 넣는다.
       * 실제 전환은 global.css의 미디어쿼리가 그 변수를 꺼내 쓰는 방식이라
       * 클라이언트 JS가 필요 없다.
       */
      themes: {
        light: 'github-light',
        dark: 'github-dark',
      },
      wrap: false,
    },
  },

  vite: {
    plugins: [tailwindcss()],
  },
});
