import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

/**
 * 글 컬렉션.
 *
 * 이 스키마가 데이터베이스 제약 조건 역할을 한다. frontmatter에 오타가 있거나
 * 필수 필드가 없으면 빌드가 실패하고, 여기 정의가 .astro/content.d.ts에
 * TypeScript 타입으로 자동 생성돼 post.data.* 자동완성이 붙는다.
 */
const posts = defineCollection({
  // base 아래에서 pattern에 맞는 파일을 읽는다.
  // '**/*.md'라 하위 폴더까지 재귀 탐색하므로 나중에 posts/2026/08/ 처럼
  // 정리해도 그대로 동작한다 (라우트를 [...slug]로 잡아둔 이유와 짝을 이룸).
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),

  /*
   * schema를 객체가 아니라 함수로 쓰는 이유 — image() 헬퍼를 받기 위해서다.
   * 객체 형태로는 frontmatter의 이미지 경로를 검증·변환할 수 없다.
   */
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      description: z.string(),

      // z.date()가 아니라 z.coerce.date()를 쓴다.
      // YAML frontmatter의 날짜는 인용부호 유무에 따라 문자열로 넘어올 수 있는데
      // coerce가 이를 Date로 변환해준다. 덕분에 쓰는 쪽에서
      // post.data.pubDate.getFullYear() 처럼 Date 메서드를 바로 쓸 수 있다.
      pubDate: z.coerce.date(),
      updatedDate: z.coerce.date().optional(),

      // .optional()이 아니라 .default([])를 쓴다.
      // optional은 타입이 string[] | undefined가 되어 쓰는 곳마다 물음표가 필요하다.
      // default를 주면 항상 string[]이라 post.data.tags.map(...)이 그냥 된다.
      tags: z.array(z.string()).default([]),

      // 초안. 개발 중에는 보이고 프로덕션 빌드에서만 제외한다 (utils/posts.ts).
      draft: z.boolean().default(false),

      /*
       * 목록의 대표 이미지. 없는 글도 있으므로 optional이다.
       *
       * image()가 경로를 검증하고 메타데이터(width·height·format)로 바꿔주므로
       * <Image>에 그대로 넘길 수 있다. 파일이 없으면 빌드가 실패한다.
       *
       * alt는 두지 않는다 — 카드에서 이미지 바로 옆에 제목이 링크로 있어
       * 스크린리더가 같은 내용을 두 번 읽게 된다. 장식으로 취급해 alt=""로 내보낸다.
       */
      cover: image().optional(),
    }),
});

// 이 export 이름은 규약이다. 다른 이름으로 내보내면 Astro가 찾지 못한다.
// 키('posts')가 getCollection('posts')에 쓰는 문자열이 된다.
export const collections = { posts };
