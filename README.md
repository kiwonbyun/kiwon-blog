# 변기원 블로그

마크다운 파일을 저장소에 올리면 정적 HTML로 빌드돼 배포되는 개인 블로그.
데이터베이스가 없고, 클라이언트로 내려가는 자바스크립트도 없다.

- **Astro 7** (`output: 'static'` 기본값)
- **Tailwind CSS 4** + `@tailwindcss/typography`
- **Pretendard Variable** dynamic subset (자가 호스팅)
- **Cloudflare Pages** 배포

---

## 글 쓰는 방법

### 1. 파일을 만든다

`src/content/posts/` 아래에 `.md` 파일을 만든다. **파일명이 그대로 URL이 된다.**

```
src/content/posts/hello-astro.md   →   /posts/hello-astro/
```

하위 폴더로 정리해도 동작한다. 라우트가 `[...slug]`로 잡혀 있어 슬래시가 포함된
경로를 받는다.

```
src/content/posts/2026/08/hello.md   →   /posts/2026/08/hello/
```

### 2. 프론트매터를 채운다

```yaml
---
title: '글 제목'
description: '목록 카드와 OG 태그, RSS에 쓰이는 한 줄 요약.'
pubDate: 2026-08-27
updatedDate: 2026-08-28    # 선택 — 있으면 "수정" 표기가 붙는다
tags: ['astro', 'blog']    # 선택 — 기본값 []
draft: false               # 선택 — 기본값 false
---
```

| 필드 | 필수 | 비고 |
| --- | --- | --- |
| `title` | 필수 | |
| `description` | 필수 | 글 상세에서 리드 문단으로도 쓰인다 |
| `pubDate` | 필수 | 표시는 한국 시간 기준 |
| `updatedDate` | 선택 | |
| `tags` | 선택 | **영문 소문자 권장** (아래 참고) |
| `draft` | 선택 | `true`면 배포에서 제외, 로컬에서는 보인다 |

**필드를 빠뜨리거나 오타를 내면 빌드가 실패한다.** 스키마 검증이 데이터베이스
제약 조건 역할을 하므로, 잘못된 글이 배포되는 경로가 없다.

```
[InvalidContentEntryDataError] posts → hello-astro data does not match collection schema.
  title: Required
```

### 3. 올린다

```bash
git add src/content/posts/새글.md
git commit -m "post: 새 글"
git push
```

푸시하면 Cloudflare가 빌드해 배포한다. 목록·태그 페이지·RSS·사이트맵은 자동으로
갱신되므로 따로 손댈 것이 없다.

### 태그에 대해

한글 태그도 동작하지만 URL이 길어진다.

```
#회고  →  /tags/%ED%9A%8C%EA%B3%A0/
```

영문 소문자를 권장한다. 태그 목록 페이지는 없고, 글에 달린 태그를 눌러
해당 태그 페이지로 들어가는 경로만 있다.

---

## 로컬 개발

**Node 버전을 먼저 맞춰야 한다.** 이 머신의 기본값은 Node 20인데 Astro 7은
22.12 이상을 요구한다.

```bash
nvm use          # .nvmrc를 읽어 24.20.0으로 전환
npm install
npm run dev      # http://localhost:4321
```

| 명령 | 설명 |
| --- | --- |
| `npm run dev` | 개발 서버 (초안도 보인다) |
| `npm run build` | `dist/`에 정적 파일 생성 |
| `npm run preview` | 빌드 결과를 정적 서버로 확인 |
| `npx astro sync` | 콘텐츠 타입 재생성 (자동완성이 안 될 때) |

`astro preview`는 백그라운드 데몬으로 돈다. 터미널에서 `Ctrl+C`를 눌러도 남아 있고
포트가 점유되면 조용히 다음 포트로 옮겨가므로, 이상하면 상태를 확인한다.

```bash
npx astro preview status
npx astro preview stop
```

---

## 배포

### Cloudflare Pages 대시보드 설정값

저장소를 연결하고 아래 두 값만 넣으면 된다.

| 항목 | 값 |
| --- | --- |
| Build command | `npm run build` |
| Build output directory | `dist` |

**Node 버전은 설정할 필요가 없다.** 빌드 이미지가 저장소의 `.nvmrc`를 읽는다.

### 도메인이 정해지면

`src/consts.ts`의 `SITE_URL` 한 줄만 고친다. canonical · OG 태그 · RSS · 사이트맵 ·
`robots.txt`가 모두 이 값을 참조한다.

```ts
export const SITE_URL = 'https://kiwon.pages.dev'; // ← 이 줄
```

### CLI로 배포하려면

`wrangler.jsonc`가 준비되어 있다. 대시보드 연동을 쓰면 필요하지 않다.

```bash
npm run build && npx wrangler deploy
```

---

## 고칠 곳

| 무엇을 | 어디서 |
| --- | --- |
| 사이트 제목 · 설명 · 도메인 · GitHub 주소 | `src/consts.ts` |
| 색 팔레트 (라이트/다크) | `src/styles/global.css`의 `:root` |
| 본문 활자 크기 · 행간 | `src/styles/global.css`의 `.prose` |
| 코드 하이라이팅 테마 | `astro.config.mjs`의 `shikiConfig` |
| 헤더 메뉴 | `src/components/Header.astro`의 `links` |
| About 본문 | `src/pages/about.astro` (주석으로 구간 표시) |

색은 `:root` 변수를 `@theme`이 참조하는 구조라, 변수 값만 바꾸면 라이트/다크가
함께 바뀐다. 컴포넌트에는 `dark:` 클래스가 없다.

---

## 구조

```
src/
├── consts.ts              사이트 전역 상수
├── content.config.ts      컬렉션 스키마 (Zod)
├── content/posts/         ★ 글은 여기에
├── utils/posts.ts         draft 필터 · 정렬 · 태그 수집
├── layouts/
│   ├── BaseLayout.astro   head · meta · OG · 폰트
│   └── PostLayout.astro   글 상세
├── components/
├── pages/
│   ├── index.astro        글 목록
│   ├── posts/[...slug].astro
│   ├── tags/[tag].astro
│   ├── about.astro
│   ├── 404.astro
│   ├── rss.xml.ts
│   └── robots.txt.ts
└── styles/global.css
```

설계 배경과 결정 근거는 [PLAN.md](./PLAN.md)에 남겨두었다.
