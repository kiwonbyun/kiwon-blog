// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import { SITE_URL } from './src/consts.ts';

// https://astro.build/config
export default defineConfig({
  // canonical · OG 태그 · RSS · sitemap이 절대 URL을 만들 때 쓴다.
  // 이 값이 없으면 Astro.site가 undefined가 되어 meta 태그가 상대경로로 나간다.
  site: SITE_URL,

  vite: {
    plugins: [tailwindcss()],
  },
});
