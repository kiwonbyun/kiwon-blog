/**
 * 사이트 전역 상수.
 * astro.config.mjs · RSS · OG 태그 · 푸터가 모두 이 파일을 참조한다.
 * 값을 바꿀 일이 생기면 여기만 고친다.
 */

/** 배포 도메인. 끝에 슬래시를 붙이지 않는다 (경로를 이어 붙일 때 //가 된다). */
export const SITE_URL = 'https://kiwon-blog.pages.dev';

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
