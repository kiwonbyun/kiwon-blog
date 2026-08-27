/**
 * 본문의 외부 링크를 새 탭에서 열도록 표시하는 Sätteri hast 플러그인.
 *
 * Astro 7의 기본 마크다운 처리기인 Sätteri는 remark/rehype 플러그인을 받지 않는다.
 * (rehype-external-links를 쓰려면 처리기를 unified로 되돌려야 하는데, 그러면
 * Sätteri의 속도와 GFM·heading id 내장 기능을 함께 잃는다.)
 * 대신 hastPlugins로 HTML 트리를 직접 손볼 수 있어서, 필요한 동작만 짧게 구현한다.
 *
 * 내부 링크는 건드리지 않는다. 같은 사이트 안에서 이동하는데 새 탭이 열리면
 * 뒤로 가기가 끊기고 탭이 쌓인다.
 *
 * rel="noopener noreferrer"를 함께 붙이는 이유 — target="_blank"만 주면 새 탭이
 * window.opener로 원래 페이지를 조작할 수 있고, 리퍼러로 방문 경로가 넘어간다.
 */
export function externalLinks(siteUrl) {
  const selfHost = safeHost(siteUrl);

  return {
    name: 'external-links',
    element: {
      // Rust 쪽에서 태그로 먼저 걸러 넘겨주므로 <a>만 순회한다.
      filter: ['a'],
      visit(node) {
        const href = node.properties?.href;
        if (typeof href !== 'string') return;

        // 앵커(#…), 루트 상대(/…), 상대경로(./…), mailto: 등은 모두 내부 취급.
        if (!/^https?:\/\//i.test(href)) return;

        // 절대 URL이지만 내 도메인을 가리키는 경우도 내부다.
        if (selfHost && safeHost(href) === selfHost) return;

        return {
          ...node,
          properties: {
            ...node.properties,
            target: '_blank',
            rel: 'noopener noreferrer',
          },
        };
      },
    },
  };
}

function safeHost(url) {
  try {
    return new URL(url).host;
  } catch {
    return '';
  }
}
