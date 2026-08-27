# 개인 블로그 구축 계획 — Astro 7 정적 사이트

> 작성일: 2026-08-27 · 상태: **구현 완료** (1~9단계). 남은 것은 원격 저장소 생성·배포 연결.
>
> 이 문서는 결정 근거를 남긴 기록이다. 현재 사용법은 [README.md](./README.md)를 본다.

## Context

**요구사항 (사용자 명시)**
1. DB를 두지 않는다 — 콘텐츠는 git에 올리는 md 파일이 전부
2. md를 웹에서 깔끔하게 렌더링
3. 모든 페이지를 완성된 `index.html`로 내려보내 빠르게 (SSR/CSR 아님)

**의도한 결과**: md 파일을 커밋·push하면 그 글이 정적 HTML로 빌드돼 배포되는 파이프라인. 글 쓰는 것 외에 어떤 운영 작업도 필요 없는 상태.

---

## 결정 사항

구현에 필요한 선택은 모두 확정됐다. 아래 표가 단일 진실 공급원이다.

| 항목 | 결정 |
|---|---|
| 프레임워크 | **Astro 7.2.8**, `output: 'static'` (기본값 그대로) |
| 스타일링 | **Tailwind CSS 4** + `@tailwindcss/typography` |
| 폰트 | **Pretendard Variable dynamic subset** 자가호스팅 — `pretendard` 패키지 CSS를 Vite로 번들 |
| 사이트 제목 | `kiwon` |
| 사이트 설명 | `개발 기록과 생각` |
| 저자 표기 | `kiwon` |
| URL 구조 | `src/content/posts/hello.md` → `/posts/hello/` |
| 홈(`/`) | **글 목록만.** 인트로·히어로 없음 |
| 다크모드 | `prefers-color-scheme` 자동 추종. 토글 버튼 없음 → JS 0KB 유지 |
| 공개 링크 | **GitHub `kiwonbyun`(개인 계정)만.** 이메일 비공개, 푸터에 RSS 링크 노출 안 함 |
| 헤더 내비 | 홈 / 태그 / About (RSS 링크 제외) |
| 배포 | **Cloudflare Pages** — git push 시 자동 빌드 |
| 언어·날짜 | `<html lang="ko">`, 날짜는 `2026년 8월 27일` |
| 패키지 매니저 | npm |
| **Node 버전** | **24.20.0** = Active LTS(Krypton), `.nvmrc`로 고정. Astro 7이 `>=22.12.0`, 하위 의존성 undici가 `>=22.19.0`을 요구 — 머신 기본값 v20.19.3으로는 스캐폴딩부터 실패. nvm `default` alias는 회사 작업용 `20`으로 그대로 둔다 |
| git 저자 | **이 레포만** `kiwonbyun` / `bkw9603@gmail.com`. 전역 설정(회사 계정)은 건드리지 않는다 |

**RSS 처리 주의**: 피드 자체는 생성하되(`/rss.xml`) 푸터·헤더에 링크를 노출하지 않는다. 단, `<head>`의 `<link rel="alternate" type="application/rss+xml">`은 넣는다 — 피드 리더의 자동 발견용이고 화면에는 보이지 않는다.

**회사/개인 계정 분리 (중요)**: 이 머신은 회사 계정으로 세팅되어 있다. 개인 프로젝트이므로 세 곳을 모두 분리해야 한다.

| 대상 | 현재 (회사) | 이 레포에서 쓸 것 |
|---|---|---|
| git `user.name` | `kiwon-swing` (전역) | `kiwonbyun` (레포 로컬) |
| git `user.email` | `kiwon@theswing.co.kr` (전역) | `bkw9603@gmail.com` (레포 로컬) |
| `gh` CLI 인증 | `kiwon-swing` | `kiwonbyun`으로 전환 필요 |

git config는 `--local`로 설정하므로 전역 회사 설정에 영향이 없다. **`gh` CLI 쪽이 함정이다** — 지금 인증이 회사 계정이라 이 상태로 리포를 만들면 회사 계정 소유로 생성된다. 원격 리포 생성 전에 계정을 전환해야 하고, 이건 인터랙티브 로그인이라 사용자가 직접 실행해야 한다:

```
! gh auth switch          # 이미 개인 계정이 등록돼 있으면 전환만
! gh auth login           # 등록돼 있지 않으면 개인 계정 추가
```


**아직 미정 (구현을 막지 않음)**
- **도메인** — `src/consts.ts`의 `SITE_URL` 한 줄. 임시로 `https://kiwon.pages.dev`를 넣고 확정 시 교체
- **About 본문 문구** — 무난한 초안을 넣고 직접 고치도록 주석 표시. 자기소개는 대신 쓸 수 없는 영역
- **Cloudflare 프로젝트명** — 기본은 `log-storage`(레포명). 배포 단계에서 확정

---

## 검증된 사실 (Astro 7 기준, 공식 문서 확인)

내 학습 데이터보다 Astro 버전이 앞서 있어 아래는 문서에서 직접 확인한 내용이다. **Astro 5/6 시절 예제와 다른 부분이 있으므로 구현 시 이 형태를 따른다.**

| 항목 | Astro 7의 현재 형태 |
|---|---|
| 콘텐츠 설정 파일 | `src/content.config.ts` (구 `src/content/config.ts` 아님) |
| 로더 | `import { glob } from 'astro/loaders'` — Content Layer API |
| Zod | `import { z } from 'astro/zod'` |
| md → HTML | `import { render } from 'astro:content'` → `const { Content, headings } = await render(entry)` |
| 마크다운 처리기 | **Sätteri** (Rust). Astro 7의 기본값. GFM·smart punctuation·heading ID·수식·wikilinks **내장** — remark/rehype 플러그인 불필요 |
| 코드 하이라이팅 | Shiki 여전히 기본. `markdown.shikiConfig.themes: { light, dark }`로 듀얼 테마 |
| Tailwind | `@tailwindcss/vite` 플러그인 (v4). 구 `@astrojs/tailwind`는 Tailwind 3 레거시 전용 |
| Tailwind 플러그인 등록 | JS config 아님 — CSS에 `@plugin "@tailwindcss/typography";` |
| Fonts API | stable(`fontProviders.*` + `<Font>`)이지만 **이번엔 쓰지 않는다** — 자체 `@font-face`를 생성해 dynamic subset의 unicode-range 분할과 충돌 |
| Pretendard 패키지 | `pretendard@1.3.9`. `@fontsource/pretendard@5.3.0`도 있으나 variable 버전이 없어 미채택 |
| dynamic subset 실측 | `dist/web/variable/pretendardvariable-dynamic-subset.css` = 56KB, `@font-face` 92개, woff2 92개 합계 **2.82MB** |
| **전송량 실측 (3단계에서 측정)** | 한국어 기술 블로그 글 972자(고유 문자 243개) → **조각 12개 / 307KB**. 통짜 variable(2007KB) 대비 **15%**. 조각이 빈도순으로 나뉘어 있어 글이 길어져도 전송량이 거의 늘지 않는다(113자 테스트 페이지도 311KB로 사실상 동일) |
| 폰트 CSS 내용 | `font-family: 'Pretendard Variable'`, `font-weight: 45 920`(가변), `font-display: swap` **이미 포함** |
| Cloudflare 정적 배포 | **어댑터 불필요.** static output은 `dist/`를 그대로 올림 |

Sätteri 내장 기능 덕에 목차·GFM 테이블·heading 앵커를 위한 추가 의존성이 0이다.

---

## 디렉토리 구조

```
log-storage/
├── astro.config.mjs
├── package.json
├── tsconfig.json
├── .gitignore
├── README.md                       # 배포 설정값·글 쓰는 방법 기록
├── wrangler.jsonc                  # CLI 배포용 (대시보드 연동만 쓸 거면 미사용)
├── public/
│   ├── favicon.svg
│   └── robots.txt
└── src/
    ├── consts.ts                   # 사이트 제목·설명·저자·URL·GitHub — 단일 진실 공급원
    ├── content.config.ts           # 컬렉션 스키마 (DB 스키마 역할)
    ├── styles/global.css           # Tailwind + typography + 폰트 변수 + Shiki 다크 대응
    ├── utils/posts.ts              # draft 필터 + 최신순 정렬 (3곳에서 재사용)
    ├── layouts/
    │   ├── BaseLayout.astro        # html/head/meta/OG + 폰트 CSS import + Header/Footer
    │   └── PostLayout.astro        # 글 상세 (prose 본문, 날짜, 태그, 목차)
    ├── components/
    │   ├── Header.astro
    │   ├── Footer.astro
    │   ├── PostCard.astro
    │   ├── FormattedDate.astro
    │   └── TableOfContents.astro
    ├── pages/
    │   ├── index.astro             # 홈 = 글 목록 (인트로 없음)
    │   ├── posts/[...slug].astro   # 글 상세 (getStaticPaths)
    │   ├── tags/index.astro        # 태그 전체
    │   ├── tags/[tag].astro        # 태그별 목록
    │   ├── about.astro
    │   ├── 404.astro
    │   └── rss.xml.js
    └── content/posts/              # ★ 앞으로 md만 여기에 추가하면 끝
        ├── hello-astro.md
        ├── why-no-database.md
        └── markdown-showcase.md    # 렌더링 확인용 (코드·테이블·인용·목록·각주)
```

---

## 핵심 파일 내용

### `src/consts.ts` — 값을 바꾸는 유일한 지점

```ts
export const SITE_URL = 'https://kiwon.pages.dev';  // 도메인 확정 시 이 줄만 교체
export const SITE_TITLE = 'kiwon';
export const SITE_DESCRIPTION = '개발 기록과 생각';
export const AUTHOR = 'kiwon';
export const GITHUB_URL = 'https://github.com/kiwonbyun';
```

`astro.config.mjs`·RSS·OG 태그·푸터가 전부 이걸 참조한다. 이메일은 어느 쪽도 넣지 않는다(비공개 결정) — 회사 이메일은 물론이고 개인 이메일도 사이트에 노출하지 않는다.

### `src/content.config.ts` — 파일이 DB를 대신하는 지점

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
    updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

export const collections = { posts };
```

frontmatter 오타·타입 오류·필수 필드 누락이 **빌드 타임에 에러로 잡힌다.** 이게 DB 제약조건 역할이고, `post.data.title`에 타입도 자동 생성된다.

### `astro.config.mjs`

```js
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import sitemap from '@astrojs/sitemap';
import { SITE_URL } from './src/consts.ts';

export default defineConfig({
  site: SITE_URL,              // RSS·sitemap의 절대 URL 생성에 필수
  integrations: [sitemap()],
  markdown: {
    shikiConfig: {
      themes: { light: 'github-light', dark: 'github-dark' },
    },
  },
  vite: { plugins: [tailwindcss()] },
});
```

`output`은 명시하지 않는다 — 기본값이 `'static'`이고, 그게 요구사항 3번이다. `fonts` 블록은 두지 않는다(아래 폰트 섹션 참조).

### 폰트 — Pretendard Variable dynamic subset

`pretendard`를 **devDependency**로 설치하고, CSS를 `BaseLayout`에서 import해 Vite가 woff2를 번들에 포함시킨다.

```astro
---
// src/layouts/BaseLayout.astro
import 'pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css';
import '../styles/global.css';
import { SITE_TITLE } from '../consts';
---
<head>
  <link rel="alternate" type="application/rss+xml" title={SITE_TITLE} href="/rss.xml" />
</head>
```

CSS 안의 `src: url(./woff2-dynamic-subset/...)`가 상대경로이므로 Vite가 92개 woff2를 해석해 `dist/_astro/`로 해시 파일명과 함께 복사한다. 폰트 바이너리를 레포에 커밋하지 않아도 되고 캐시 무효화도 자동으로 처리된다.

**동작 원리와 트레이드오프**

`dist`에는 92개 조각(2.82MB)이 모두 들어가지만, **방문자는 그 페이지에 실제로 등장하는 글자가 속한 조각만 받는다.** 브라우저가 `unicode-range`를 보고 필요한 파일만 요청하기 때문이다. 한국어 본문 한 페이지면 보통 조각 몇 개로 끝난다. 즉 `dist` 용량과 방문자 전송량은 별개이고, 여기서 중요한 건 후자다.

대가는 **preload를 걸 수 없다는 점**이다. 어느 조각이 필요한지 빌드 타임에 알 수 없다. 그래서 첫 페인트는 fallback 폰트로 나오고 폰트가 도착하면 교체된다(CSS에 `font-display: swap`이 이미 들어 있음). 이 교체가 눈에 띄지 않게 하려면 fallback을 한글 시스템 폰트로 지정해 자막 폭 차이를 줄이는 것이 관건이다 — 아래 `global.css`가 그 역할을 한다.

통짜 variable(`woff2/PretendardVariable.woff2`)은 1.96MB를 한 번에 받는다. dynamic subset은 그 대신 필요한 조각만 받으므로 통상 수십~수백 KB에 그친다. preload를 포기하는 대가로 전송량을 이만큼 줄이는 거래이고, 정적 블로그에서는 이쪽이 맞다.

### `src/styles/global.css`

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";

@theme {
  /* 폰트 도착 전에도 한글이 깨지지 않고, 폭 차이가 작은 시스템 폰트를 fallback으로 */
  --font-sans: 'Pretendard Variable', -apple-system, BlinkMacSystemFont,
    'Apple SD Gothic Neo', 'Malgun Gothic', system-ui, sans-serif;
}

/* Shiki 듀얼 테마: OS가 다크면 dark 변수로 스왑 */
@media (prefers-color-scheme: dark) {
  .astro-code,
  .astro-code span {
    color: var(--shiki-dark) !important;
    background-color: var(--shiki-dark-bg) !important;
  }
}
```

Tailwind 4의 `@theme`로 `--font-sans`를 덮어쓰면 `font-sans` 유틸리티와 `prose` 본문이 모두 Pretendard를 쓴다. 본문은 `prose dark:prose-invert`로 감싼다.

`font-weight: 45 920` 가변 폰트라 400·700을 쓰든 그 사이 아무 값을 쓰든 **추가 다운로드가 없다.** 제목 굵기를 자유롭게 조절할 수 있다.

### `src/utils/posts.ts` — 중복 방지

```ts
import { getCollection, type CollectionEntry } from 'astro:content';

export async function getPublishedPosts(): Promise<CollectionEntry<'posts'>[]> {
  const posts = await getCollection('posts', ({ data }) =>
    import.meta.env.PROD ? !data.draft : true,   // dev에선 draft도 보임
  );
  return posts.sort((a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf());
}
```

홈·태그 페이지·RSS 세 곳이 모두 이걸 쓴다. draft 규칙과 정렬 순서가 한 곳에만 존재하게 한다.

### `src/pages/posts/[...slug].astro`

```astro
---
import { render } from 'astro:content';
import { getPublishedPosts } from '../../utils/posts';
import PostLayout from '../../layouts/PostLayout.astro';

export async function getStaticPaths() {
  const posts = await getPublishedPosts();
  return posts.map((post) => ({ params: { slug: post.id }, props: { post } }));
}

const { post } = Astro.props;
const { Content, headings } = await render(post);
---
<PostLayout post={post} headings={headings}>
  <Content />
</PostLayout>
```

`getStaticPaths()`가 md 하나당 `dist/posts/<slug>/index.html` 하나를 만든다. `headings`는 Sätteri가 생성해주므로 목차용 추가 파싱이 없다.

### 태그 slug 처리

태그는 영문 소문자를 권장하되 한글 태그도 동작해야 한다. `tags/[tag].astro`의 `getStaticPaths()`에서 `encodeURIComponent`로 경로를 만들고 화면 표시에는 원문을 쓴다. 한글 태그는 URL이 `%ED%9B%84%EA%B3%A0` 형태로 길어지므로 README에 영문 태그 권장을 적어둔다.

---

## 작업 단계

각 단계 끝에서 커밋한다.

**1. 스캐폴딩 + 계정 분리**
```bash
git init
git config --local user.name  "kiwonbyun"       # 전역(회사) 설정은 그대로 둠
git config --local user.email "bkw9603@gmail.com"
git config --local --list | grep user           # 분리 확인
npm create astro@latest . -- --template minimal --no-install --no-git --typescript strict
npm install
```
빈 디렉토리이므로 덮어쓸 파일 없음(단 `PLAN.md`는 보존). `.gitignore`에 `dist/`, `node_modules/`, `.astro/` 확인.
**첫 커밋 전에 `git config --local`을 먼저 건다** — 순서가 뒤바뀌면 초기 커밋이 회사 이메일로 찍혀 나중에 rebase해야 한다.

**2. Tailwind 4 + typography**
`npx astro add tailwind` (Vite 플러그인 자동 등록) → `npm i -D @tailwindcss/typography` → `global.css` 작성.

**3. 폰트**
`npm i -D pretendard` → `BaseLayout`에서 `pretendardvariable-dynamic-subset.css` import → `@theme`로 `--font-sans` 연결(fallback 포함).
`pretendard` 패키지는 unpacked 97MB지만 `node_modules`에만 머물고 `dist`에는 실제 참조된 woff2만 들어간다. devDependency로 두는 이유도 이것 — 런타임 의존이 아니라 빌드 입력이다.

**4. 콘텐츠 계층**
`src/consts.ts`, `src/content.config.ts`, `src/utils/posts.ts` 작성.

**5. 레이아웃·컴포넌트**
`BaseLayout`(meta·OG·Twitter 카드·canonical·RSS alternate), `PostLayout`, Header/Footer/PostCard/FormattedDate/TableOfContents.
Header는 홈 / 태그 / About. Footer는 `© 2026 kiwon` + GitHub 링크.

**6. 페이지**
`index.astro`(글 목록만), `posts/[...slug].astro`, `tags/index.astro`, `tags/[tag].astro`, `about.astro`, `404.astro`.
About은 무난한 초안 + `{/* 여기부터 직접 수정 */}` 주석.

**7. 피드·SEO**
`npm i @astrojs/rss @astrojs/sitemap` → `rss.xml.js`, sitemap 인테그레이션, `public/robots.txt`(sitemap 경로 포함), `favicon.svg`.

**8. 샘플 글 3개**
`markdown-showcase.md`에 코드블록·테이블·인용·중첩 목록·각주를 모두 넣어 렌더링 스타일을 한 번에 검수할 수 있게 한다.

**9. Cloudflare Pages 설정 파일**
`wrangler.jsonc`:
```jsonc
{
  "name": "log-storage",
  "compatibility_date": "2026-08-27",
  "assets": { "directory": "./dist" }
}
```
`README.md`에 대시보드 연동 설정값 기록: build command `npm run build`, output directory `dist`. **Node 버전은 별도 설정이 필요 없다** — Cloudflare Pages 빌드 이미지가 레포의 `.nvmrc`를 읽으므로 로컬과 CI가 자동으로 24.20.0으로 일치한다(빌드 이미지 기본값은 22.16.0이고 그보다 최신 버전도 허용). 그리고 "글 쓰는 방법"(md 추가 → frontmatter 형식 → push) 섹션.

> **범위 경계**: 원격 리포지토리 생성, 첫 push, Cloudflare 프로젝트 연결은 외부에 공개되는 작업이라 **별도로 확인받고 진행한다.** 이 계획의 범위는 로컬에서 빌드가 통과하는 상태까지다.
>
> 그 단계로 넘어가기 전에 **`gh` CLI 계정 전환이 선행되어야 한다** — 현재 인증은 회사 계정(`kiwon-swing`)이므로 그대로 리포를 만들면 회사 소유로 생성된다. 인터랙티브 로그인이라 사용자가 직접 `! gh auth switch`(또는 `! gh auth login`)를 실행해야 하고, `gh api user --jq .login`이 `kiwonbyun`으로 나오는지 확인한 뒤 진행한다.

---

## 검증

**요구사항 3번(완성된 index.html)이 실제로 지켜지는지가 핵심 검증이다.**

```bash
npm run dev          # localhost:4321 — 목록·상세·태그·About·404 육안 확인
npm run build        # 빌드 통과 + 스키마 검증 통과
```

빌드 산출물 검사:

```bash
find dist -name "*.html" | sort           # dist/index.html, dist/posts/<slug>/index.html 등 존재
grep -c "본문에만 있는 문장" dist/posts/hello-astro/index.html   # ≥1 이면 HTML에 본문이 박혀 있음
find dist -name "*.js" | wc -l            # 0 이어야 JS 0KB 달성
du -sh dist                               # 전체 용량
find dist -name "*.woff2" | wc -l         # 92 여야 dynamic subset 조각이 다 들어옴
npm run preview                           # 정적 서버로 최종 확인
```

- **폰트 (핵심)**: `dist`의 woff2 개수가 92개인지, 그리고 `dist/**/*.css`에 `unicode-range`가 살아있는지 확인. 그다음 **`npm run preview`로 띄워 브라우저 devtools 네트워크 탭에서 한 페이지 로드 시 실제로 받는 woff2 개수와 합계 용량을 측정한다.** 이게 진짜 확인해야 할 숫자다 — `dist` 용량(2.82MB)이 아니라 방문자 전송량. 한국어 본문 한 페이지에서 조각 몇 개 수준이면 정상
- **폰트 교체 체감**: 네트워크를 Slow 3G로 조절해 새로고침 → fallback에서 Pretendard로 바뀔 때 글자가 크게 밀리지 않는지 육안 확인. 심하면 `@theme`의 fallback 스택을 조정한다
- `dist/rss.xml`, `dist/sitemap-index.xml` 생성 확인 및 절대 URL이 `SITE_URL`로 나오는지
- **다크모드**: OS를 다크로 전환해 본문과 **코드블록 배경까지** 함께 바뀌는지 (Shiki 변수 스왑이 실제로 먹는지)
- **스키마 검증 동작 확인**: 샘플 글 하나에서 `title`을 일부러 지우고 `npm run build` → 에러로 실패해야 정상. 확인 후 되돌린다. (DB 없이 무결성을 지키는 장치가 살아있는지 보는 테스트)
- **md 추가 플로우 확인**: 새 md 파일 하나를 만들고 빌드 → 목록·RSS·sitemap에 자동 반영되는지. 이게 앞으로의 유일한 운영 작업이다
- **이메일·회사 정보 비노출 확인**: 아래가 모두 비어야 한다
  ```bash
  grep -ri "theswing\|kiwon-swing\|bkw9603\|@gmail\|\.kr" dist/ ; echo "exit=$?"   # 결과 없음 = 정상
  ```
- **커밋 저자 확인**: `git log -1 --format='%an <%ae>'` → `kiwonbyun <bkw9603@gmail.com>`. 회사 이메일이 찍혀 있으면 push 전에 고친다

---

## 이후 (이번 범위 아님)

필요해지면 붙일 것들. 지금은 넣지 않는다.
- 클라이언트 사이드 글 검색 (Pagefind — 정적 인덱스 방식이라 DB 없는 구조 유지)
- 다크모드 토글 버튼 (localStorage)
- 댓글 (Giscus — GitHub Discussions 기반, 역시 DB 불필요)
- 조회수, OG 이미지 자동 생성, 글 목록 페이지네이션

---

## 구현하며 계획과 달라진 점

계획을 세운 시점에 몰랐거나, 만들면서 더 나은 방법을 찾은 부분들.

| 항목 | 계획 | 실제 | 이유 |
|---|---|---|---|
| Node 버전 | 20 이상 | **24.20.0** | Astro 7이 `>=22.12.0`을 요구해 스캐폴딩부터 실패했다. undici가 `>=22.19.0`을 원해 Active LTS인 24로 올렸다 |
| 날짜 처리 | `Intl.DateTimeFormat` + `timeZone: 'UTC'` | **date-fns 4 + `@date-fns/tz`**, `Asia/Seoul` | 시간대를 상수 한 곳에서 관리하고, 시간까지 적은 글도 한국 기준으로 표기하려면 라이브러리가 낫다 |
| `robots.txt` | `public/` 정적 파일 | **`src/pages/robots.txt.ts` 엔드포인트** | 정적 파일에는 변수를 쓸 수 없어 sitemap 주소가 하드코딩된다. 엔드포인트면 `SITE_URL`을 참조하므로 도메인 확정 시 고칠 곳이 한 줄로 유지된다 |
| 다크모드 구현 | 컴포넌트마다 `dark:` 클래스 | **`@theme` + `:root` 변수 우회** | 색 유틸리티가 미디어쿼리로 자동 전환된다. `.astro` 파일에서 `dark:`가 전부 사라지고 `dark:prose-invert`도 불필요해졌다 |
| 태그 목록 페이지 | `tags/index.astro` 포함 | **제거** | 필요 없다는 판단. `getAllTags`의 `count` 필드도 함께 정리했다 |
| 사이트명 | `kiwon` | **`변기원 블로그`** (저자 표기는 `변기원`) | 헤더의 넓은 자간·`uppercase`도 한글에 맞게 조정했다 |
| 한글 세리프 | 검토 대상 아님 | **보류** | 전송량을 재보니 Pretendard 307KB에 제목용 세리프를 얹으면 614~708KB로 2배 이상 늘어난다 |
| Prettier·ESLint | 계획에 없음 | **도입하지 않음** | 검토했으나 TypeScript 6.0.x로 버전이 묶이는 제약이 있어 보류했다 |

## 검증 최종 결과

```
HTML 11페이지 · 클라이언트 JS 0개 · md 3개 · DB 의존성 0개
폰트  woff2 92조각 중 페이지당 12~14개만 전송 (307~417 KB, 전체의 11~14%)
용량  dist 3.2 MB (폰트 2.82 MB · CSS 72.6 KB · HTML 60.2 KB)
개인정보 회사 계정·이메일 노출 0건
커밋  kiwonbyun <bkw9603@gmail.com>
```

스키마 검증은 `title` 삭제와 `pubDate`에 비날짜 값을 넣어 빌드가 실패하는 것으로
확인했다. GFM 요소(표·각주·작업목록·중첩인용)는 마크다운 관련 의존성 0개 상태에서
모두 렌더된다 — Astro 7의 Sätteri 내장 기능.
