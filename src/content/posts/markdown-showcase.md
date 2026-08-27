---
title: '마크다운 렌더링 점검표'
description: '이 블로그가 지원하는 마크다운 요소를 한자리에 모아 스타일을 확인하는 글.'
pubDate: 2026-08-14
tags: ['markdown', 'blog']
draft: false
---

글을 쓰다 만나는 요소를 한 번에 확인하려고 만든 글이다. 스타일을 고칠 때 이 페이지를
열어놓고 비교하면 빠뜨리는 곳이 줄어든다.

## 문단과 강조

본문은 이런 크기와 행간으로 나온다. 한글과 English와 숫자 12345가 섞여도 기준선이
흔들리지 않아야 한다. **굵게 강조한 부분**과 *기울인 부분*, 그리고 ~~지운 부분~~이
서로 구별되어야 한다.

인라인 코드는 `npm run build`처럼 배경이 붙는다. 백틱이 화면에 보이면 잘못된 것이다.
파일 경로 `src/content/posts/`나 변수명 `--font-sans`도 같은 취급을 받는다.

문단 사이 여백은 이 정도다. 두 문단이 붙어 보이지 않고, 그렇다고 너무 벌어져서
흐름이 끊기지도 않는 지점을 찾아야 한다.

## 목록

순서 없는 목록과 중첩:

- 첫 항목
- 두 번째 항목
  - 한 단계 들여쓴 항목
  - 여기도 마커와 여백이 유지되어야 한다
    - 두 단계까지 내려간 경우
- 마지막 항목

순서 있는 목록:

1. 번호가 붙는다
2. 두 번째
   1. 중첩되면 번호 체계가 바뀐다
   2. 여기도 확인
3. 세 번째

작업 목록도 쓸 수 있다. GFM 기능인데 Sätteri에 내장이라 플러그인이 필요 없다.

- [x] 완료한 항목
- [ ] 남은 항목
- [ ] 체크박스 정렬이 텍스트와 맞는지

## 인용

> 인용문은 좌측 규칙선으로만 구분한다. 장식 따옴표와 이탤릭을 끄고 본문과 같은
> 서체를 쓰되 색을 약하게 해서 위계를 만들었다.

중첩 인용도 확인한다.

> 바깥 인용문.
>
> > 안쪽 인용문. 규칙선이 두 겹으로 보여야 한다.

## 코드

짧은 코드블록:

```bash
npm run build
npx astro sync
```

언어별 하이라이팅과 긴 줄의 가로 스크롤:

```ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { posts };
```

CSS도 확인한다. 주석 색이 코드와 충분히 구별되어야 한다.

```css
@media (prefers-color-scheme: dark) {
  .astro-code,
  .astro-code span {
    /* Shiki가 넣어둔 다크 색으로 스왑 */
    color: var(--shiki-dark) !important;
    background-color: var(--shiki-dark-bg) !important;
  }
}
```

언어를 지정하지 않은 블록:

```
하이라이팅 없이 고정폭으로만 나온다.
로그나 출력을 붙일 때 쓴다.
```

## 표

| 항목 | 방식 | 전송량 |
| --- | --- | --- |
| 본문 폰트 | Pretendard Variable dynamic subset | 307 KB |
| 코드 하이라이팅 | Shiki 듀얼 테마 | 0 KB |
| 클라이언트 JS | 없음 | 0 KB |

정렬을 지정한 표:

| 왼쪽 | 가운데 | 오른쪽 |
| :--- | :---: | ---: |
| 텍스트 | 텍스트 | 1,234 |
| 긴 내용이 들어가는 칸 | 짧음 | 56 |

## 구분선과 링크

아래는 수평선이다.

---

링크는 색이 아니라 얇은 밑줄로 구분한다. [Astro 문서](https://docs.astro.build/)처럼
본문 안에 섞여도 읽기를 방해하지 않아야 하고, 커서를 올리면 밑줄이 진해진다.

## 각주

각주도 GFM 기능이라 그냥 쓸 수 있다.[^1] 여러 개를 달아도 번호가 순서대로 붙는다.[^2]

[^1]: 각주 내용은 글 맨 아래에 모인다.
[^2]: 본문에서 각주 번호를 누르면 여기로 이동하고, 되돌아가는 링크도 자동으로 붙는다.
