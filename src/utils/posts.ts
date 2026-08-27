import { getCollection, type CollectionEntry } from 'astro:content';

/**
 * 글 하나의 타입. content.config.ts의 Zod 스키마에서 자동 추론된다.
 * 컴포넌트 props 타입으로 쓰기 편하도록 별칭을 둔다.
 */
export type Post = CollectionEntry<'posts'>;

/**
 * 공개된 글을 최신순으로 반환한다.
 *
 * 홈 목록 · 태그별 목록 · RSS 세 곳이 모두 이 함수를 쓴다.
 * draft 판정 기준과 정렬 순서가 한 곳에만 존재하게 하려는 것 —
 * 세 곳에 흩어지면 나중에 규칙이 갈린다.
 */
export async function getPublishedPosts(): Promise<Post[]> {
  const posts = await getCollection('posts', ({ data }) =>
    // 개발 중에는 초안도 보여야 글을 쓰면서 확인할 수 있다.
    // 프로덕션 빌드에서만 걸러내므로 배포물에는 초안이 들어가지 않는다.
    import.meta.env.PROD ? !data.draft : true,
  );
  console.log(posts)

  // pubDate가 z.coerce.date()로 Date이므로 valueOf()로 바로 비교된다.
  // 문자열이었다면 파싱을 거쳐야 했다.
  return posts.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
}

/**
 * 공개된 글에 쓰인 태그를 중복 없이 이름 순으로 반환한다.
 *
 * 태그 페이지의 getStaticPaths가 이 목록으로 경로를 만든다.
 * 즉 아무 글도 달지 않은 태그는 페이지가 생기지 않는다.
 */
export async function getAllTags(): Promise<string[]> {
  const posts = await getPublishedPosts();
  const tags = new Set(posts.flatMap((post) => post.data.tags));

  // 한글 태그도 사전 순으로 정렬되도록 로케일을 지정한다.
  return [...tags].sort((a, b) => a.localeCompare(b, 'ko'));
}

/** 특정 태그를 가진 글만 최신순으로 반환한다. */
export async function getPostsByTag(tag: string): Promise<Post[]> {
  const posts = await getPublishedPosts();
  return posts.filter((post) => post.data.tags.includes(tag));
}
