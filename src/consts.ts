/**
 * 사이트 전역 상수.
 * astro.config.mjs · RSS · OG 태그 · 푸터가 모두 이 파일을 참조한다.
 * 값을 바꿀 일이 생기면 여기만 고친다.
 */

/** 배포 도메인. 끝에 슬래시를 붙이지 않는다 (경로를 이어 붙일 때 //가 된다). */
export const SITE_URL = 'https://kiwon-blog.bkw9603.workers.dev';

export const SITE_TITLE = '변기원 블로그';
export const SITE_DESCRIPTION = '개발 기록과 생각';
export const AUTHOR = '변기원';

/** 개인 계정 */
export const GITHUB_URL = 'https://github.com/kiwonbyun';

/**
 * 날짜 표시 기준 시간대.
 * 빌드 머신의 로컬 시간대(로컬은 KST, Cloudflare는 UTC)에 결과가 좌우되지
 * 않도록 고정한다. 이 값을 바꾸면 사이트 전체 날짜 표기가 함께 바뀐다.
 */
export const TIME_ZONE = 'Asia/Seoul';

/**
 * 컨테이너 폭.
 *
 * 두 종류로 나뉜다. 글 본문은 한 줄이 너무 길면 다음 줄 첫 글자를 찾기 어려워
 * 좁게 묶어두고, 카드 목록은 화면이 넓을수록 열을 늘려야 하므로 더 넓게 연다.
 *
 * 헤더·푸터가 이 값을 페이지에 맞춰 골라 쓰는 이유 — 한쪽만 넓히면 목록
 * 페이지에서 로고보다 카드가 바깥으로 튀어나와 어긋나 보인다. 테두리는
 * 원래 화면 전체를 가로지르므로 안쪽 정렬만 맞추면 된다.
 *
 * 클래스 문자열을 상수로 둬도 Tailwind가 이 파일을 훑어 유틸리티를 생성한다.
 */
export const READING_WIDTH = 'max-w-2xl lg:max-w-3xl xl:max-w-5xl';
export const LISTING_WIDTH =
  'max-w-2xl lg:max-w-5xl xl:max-w-7xl 2xl:max-w-[1440px]';
