#!/usr/bin/env python3
"""티스토리 글 하나를 마크다운으로 기계 변환하고 이미지를 내려받는다.

이 스크립트는 문장을 절대 손대지 않는다. HTML 태그를 마크다운 기호로 바꾸고
공백을 정리하는 일만 한다. 구조화(heading 삽입)는 사람이나 에이전트가
이 스크립트의 출력물(.raw.md)을 편집해서 하고, 그 결과가 원문과 같은지는
verify.py로 확인한다.

사용:
    python3 fetch_post.py <URL> --slug <slug> --posts-dir <dir>

출력:
    <work-dir>/<slug>.raw.md       기계 변환된 본문. 편집 금지 (비교 기준)
    <work-dir>/<slug>.meta.json    제목·날짜·태그·이미지 목록·본문 지문
    <posts-dir>/<slug>/image-N.webp  내려받아 WebP로 변환한 이미지

작업 파일을 posts 디렉토리에 두지 않는 이유 — 컬렉션 로더가 **/*.md 를 훑기 때문에
.raw.md도 글로 인식되고, frontmatter가 없어 빌드가 스키마 오류로 실패한다.
dev 서버가 떠 있으면 즉시 에러 화면이 뜬다.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.request
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"


def get(url: str, referer: str | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    if referer:
        req.add_header("Referer", referer)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def slice_body(html: str) -> str:
    """본문 컨테이너만 잘라낸다.

    경계를 정확히 잡는 것이 중요하다. 단순히 다음 </div>를 찾으면 본문이 일찍
    끊기고, 문서 끝까지 가면 '카테고리의 다른 글' 목록과 티스토리 툴바가 섞여
    들어온다. div 깊이를 세어 짝이 맞는 닫는 태그를 찾는다.
    """
    for pattern in (
        r'<div[^>]*class="[^"]*contents_style[^"]*"[^>]*>',
        r'<div[^>]*class="[^"]*tt_article_useless_p_margin[^"]*"[^>]*>',
        r'<div[^>]*class="[^"]*article_view[^"]*"[^>]*>',
    ):
        m = re.search(pattern, html)
        if not m:
            continue
        start = m.end()
        depth = 1
        for t in re.finditer(r"<(/?)div\b[^>]*>", html[start:]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                return html[start : start + t.start()]
        return html[start:]
    raise SystemExit("본문 컨테이너를 찾지 못했습니다. 티스토리 스킨 구조를 확인하세요.")


def strip_og_cards(html: str) -> str:
    """티스토리가 URL 아래에 자동으로 붙이는 OG 링크 카드를 걷어낸다.

    카드는 figure[data-og-*] 로 표시되고 내부에 제목·설명·도메인이 문단으로
    들어있다. 이를 그대로 옮기면 마크다운에 아래처럼 남는다.

        [
        Functional Software Architecture
        Functional core, imperative shell is a pattern that ...
        functional-architecture.org
        ](https://...)

    글쓴이가 쓴 문장이 아니라 플랫폼이 만든 위젯이고, 같은 URL의 일반 링크가
    바로 위에 이미 있어 중복이다. 게다가 설명은 외부 사이트의 OG 태그를 복사한
    것이라 시간이 지나면 낡는다. 관련글 목록·툴바를 제외하는 것과 같은 이유로
    본문에서 뺀다.
    """
    out: list[str] = []
    pos = 0
    for m in re.finditer(r"<figure\b([^>]*)>", html):
        if "data-og-" not in m.group(1) or m.start() < pos:
            continue
        depth, end = 1, m.end()
        for t in re.finditer(r"<(/?)figure\b[^>]*>", html[m.end() :]):
            depth += -1 if t.group(1) else 1
            if depth == 0:
                end = m.end() + t.end()
                break
        out.append(html[pos : m.start()])
        pos = end
    out.append(html[pos:])
    return "".join(out)


class ToMarkdown(HTMLParser):
    """본문 HTML을 블록 단위 마크다운으로 옮긴다."""

    BLOCK = {"p", "div", "figure", "blockquote", "pre", "ul", "ol", "li", "table", "tr"}

    def __init__(self, image_paths: list[str]):
        super().__init__(convert_charrefs=True)
        self.image_paths = image_paths
        self.img_index = 0
        self.blocks: list[str] = []
        self.buf: list[str] = []
        self.list_stack: list[str] = []
        self.li_index: list[int] = []
        self.in_pre = False
        self.pre_lang = ""
        self.pre_buf: list[str] = []
        self.quote_depth = 0
        self.table_rows: list[list[str]] = []
        self.cell: list[str] | None = None
        self.in_table = False
        self.href: str | None = None

    # ── 블록 마감 ────────────────────────────────────────────────
    def _flush(self) -> None:
        text = "".join(self.buf)
        self.buf.clear()
        # 문단 내부의 연속 공백만 정리한다. 문장 자체는 건드리지 않는다.
        # 줄 끝의 두 칸(hard break)은 남기고 그 외 연속 공백만 정리한다.
        text = re.sub(r"[ \t\u00a0]+(?!\n)", " ", text)
        text = re.sub(r"[ \t\u00a0]{3,}\n", "  \n", text)
        text = text.strip()
        if not text:
            return
        if self.quote_depth:
            text = "\n".join("> " + ln if ln else ">" for ln in text.split("\n"))
        self.blocks.append(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)

        if tag == "pre":
            self._flush()
            self.in_pre = True
            self.pre_lang = a.get("data-ke-language") or a.get("class") or ""
            self.pre_lang = self.pre_lang.split()[0] if self.pre_lang else ""
            return
        if self.in_pre:
            return

        if tag == "img":
            src = a.get("src") or a.get("data-url") or ""
            if src and self.img_index < len(self.image_paths):
                self._flush()
                self.blocks.append(f"![]({self.image_paths[self.img_index]})")
                self.img_index += 1
            return

        if tag == "br":
            # 마크다운에서 단일 개행은 공백으로 합쳐지므로 원문의 줄나눔이 사라진다.
            # 두 칸 + 개행(hard break)으로 내보내 <br>을 그대로 보존한다.
            self.buf.append("  \n")
            return

        if tag in ("strong", "b"):
            self.buf.append("**")
            return
        if tag in ("em", "i"):
            self.buf.append("*")
            return
        if tag == "code" and not self.in_pre:
            self.buf.append("`")
            return

        if tag == "a":
            self.href = a.get("href")
            self.buf.append("[")
            return

        if tag == "blockquote":
            self._flush()
            self.quote_depth += 1
            return

        if tag in ("ul", "ol"):
            self._flush()
            self.list_stack.append(tag)
            self.li_index.append(0)
            return

        if tag == "li":
            self._flush()
            return

        if tag == "table":
            self._flush()
            self.in_table = True
            self.table_rows = []
            return
        if tag == "tr" and self.in_table:
            self.table_rows.append([])
            return
        if tag in ("td", "th") and self.in_table:
            self.cell = []
            return

        if tag in self.BLOCK:
            self._flush()

    def handle_endtag(self, tag):
        if tag == "pre":
            code = unescape("".join(self.pre_buf)).strip("\n")
            self.pre_buf.clear()
            self.in_pre = False
            fence = f"```{self.pre_lang}".rstrip()
            self.blocks.append(f"{fence}\n{code}\n```")
            return
        if self.in_pre:
            return

        if tag in ("strong", "b"):
            self.buf.append("**")
            return
        if tag in ("em", "i"):
            self.buf.append("*")
            return
        if tag == "code":
            self.buf.append("`")
            return

        if tag == "a":
            self.buf.append(f"]({self.href or ''})")
            self.href = None
            return

        if tag == "blockquote":
            self._flush()
            self.quote_depth = max(0, self.quote_depth - 1)
            return

        if tag == "li":
            text = re.sub(r"[ \t ]+", " ", "".join(self.buf)).strip()
            self.buf.clear()
            if text:
                depth = max(0, len(self.list_stack) - 1)
                indent = "  " * depth
                if self.list_stack and self.list_stack[-1] == "ol":
                    self.li_index[-1] += 1
                    self.blocks.append(f"{indent}{self.li_index[-1]}. {text}")
                else:
                    self.blocks.append(f"{indent}- {text}")
            return

        if tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
                self.li_index.pop()
            return

        if tag in ("td", "th") and self.in_table and self.cell is not None:
            cellv = re.sub(r"\s+", " ", "".join(self.cell)).strip()
            if self.table_rows:
                self.table_rows[-1].append(cellv)
            self.cell = None
            return

        if tag == "table" and self.in_table:
            self.in_table = False
            rows = [r for r in self.table_rows if r]
            if rows:
                head, *rest = rows
                out = ["| " + " | ".join(head) + " |",
                       "| " + " | ".join("---" for _ in head) + " |"]
                out += ["| " + " | ".join(r) + " |" for r in rest]
                self.blocks.append("\n".join(out))
            return

        if tag in self.BLOCK:
            self._flush()

    def handle_data(self, data):
        if self.in_pre:
            self.pre_buf.append(data)
        elif self.cell is not None:
            self.cell.append(data)
        else:
            self.buf.append(data)

    def result(self) -> str:
        self._flush()
        return "\n\n".join(self.blocks).strip() + "\n"


def meta_of(html: str) -> dict:
    def pick(*patterns):
        for p in patterns:
            m = re.search(p, html)
            if m:
                return unescape(m.group(1)).strip()
        return ""

    title = pick(
        r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"',
        r"<title>([^<]*)</title>",
    )
    published = pick(
        r'<meta[^>]+property="article:published_time"[^>]+content="([^"]*)"',
        r'<time[^>]*datetime="([^"]*)"',
        r'"datePublished"\s*:\s*"([^"]*)"',
    )
    tags = re.findall(r'<meta[^>]+property="article:tag"[^>]+content="([^"]*)"', html)
    if not tags:
        tags = re.findall(r'rel="tag"[^>]*>([^<]+)<', html)
    return {
        "title": title,
        "published": published,
        "tags": [unescape(t).strip() for t in tags],
    }


def image_urls(body: str) -> list[str]:
    """본문 등장 순서대로 이미지 원본 URL을 모은다.

    티스토리는 figure > span[data-url] > img[src] 구조를 쓴다. srcset에는
    daumcdn 썸네일(리사이즈된 것)이 들어가므로 원본인 src/data-url을 쓴다.
    """
    urls: list[str] = []
    for tag in re.finditer(r"<(?:img|span)\b[^>]*>", body):
        t = tag.group(0)
        m = re.search(r'(?:\bsrc|data-url)=["\']([^"\']+)["\']', t)
        if not m:
            continue
        u = m.group(1)
        if "kakaocdn" not in u and "daumcdn" not in u:
            continue
        if "no-image" in u:
            continue
        base = u.split("?")[0]
        if any(base == x.split("?")[0] for x in urls):
            continue
        urls.append(u)
    return urls


def ext_of(url: str, blob: bytes) -> str:
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if blob[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if blob[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return ".webp"
    m = re.search(r"\.(png|jpe?g|gif|webp)(?:\?|$)", url, re.I)
    return "." + m.group(1).lower().replace("jpeg", "jpg") if m else ".png"


def to_webp(blob: bytes, ext: str) -> tuple[bytes, str]:
    """내려받은 이미지를 WebP로 바꾼다. 바꿀 수 없으면 원본을 그대로 돌려준다.

    빌드 때도 Astro가 WebP를 만들지만 그건 dist 얘기고, git에 영구히 남는 것은
    여기서 저장하는 소스다. 이미지는 이미 압축된 바이너리라 git의 delta 압축이
    먹히지 않아 커밋된 크기가 히스토리에 그대로 쌓인다. 글이 쌓일수록 늘어나는
    것은 dist가 아니라 이쪽이므로, 받는 시점에 줄여두는 것이 유일한 기회다.
    (나중에 일괄 변환하면 옛 파일이 히스토리에 남아 오히려 레포가 2배가 된다.)

    무손실과 손실(q85)을 둘 다 만들어 작은 쪽을 고른다. 평평한 UI 스크린샷은
    무손실이 더 작으면서 글자도 뭉개지지 않고, 지도·사진은 손실이 압도적으로 작다.
    다만 손실이 확실히 작을 때(무손실의 60% 이하)만 손실을 택한다 — 몇 KB 아끼려고
    스크린샷 속 글자를 뭉개는 것은 손해이기 때문이다.
    """
    if ext == ".webp":
        return blob, ext  # 이미 WebP. 다시 인코딩하면 화질만 깎인다

    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / ("in" + ext)
        src.write_bytes(blob)

        # GIF는 cwebp가 애니메이션을 못 읽는다. gif2webp가 프레임을 보존한다.
        if ext == ".gif":
            out = Path(td) / "out.webp"
            if not _run(["gif2webp", "-quiet", str(src), "-o", str(out)], out):
                return blob, ext
            return (out.read_bytes(), ".webp") if out.stat().st_size < len(blob) else (blob, ext)

        lossless, lossy = Path(td) / "ll.webp", Path(td) / "ly.webp"
        ok_ll = _run(["cwebp", "-quiet", "-lossless", "-z", "9", str(src), "-o", str(lossless)], lossless)
        ok_ly = _run(["cwebp", "-quiet", "-q", "85", "-sharp_yuv", str(src), "-o", str(lossy)], lossy)
        if not ok_ll and not ok_ly:
            return blob, ext  # cwebp가 없거나 실패 — 원본을 그대로 쓴다

        cands = []
        if ok_ll:
            cands.append((lossless.stat().st_size, lossless))
        if ok_ly and ok_ll and lossy.stat().st_size * 100 // lossless.stat().st_size <= 60:
            cands.append((lossy.stat().st_size, lossy))
        elif ok_ly and not ok_ll:
            cands.append((lossy.stat().st_size, lossy))

        size, best = min(cands)
        return (best.read_bytes(), ".webp") if size < len(blob) else (blob, ext)


def _run(cmd: list[str], out: Path) -> bool:
    """인코더를 돌리고 결과 파일이 실제로 생겼는지까지 확인한다."""
    if shutil.which(cmd[0]) is None:
        return False
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    except Exception:  # noqa: BLE001
        return False
    return out.exists() and out.stat().st_size > 0


def fingerprint(md: str) -> dict:
    """본문의 지문. verify.py가 내용 변경을 잡아낼 때 쓴다."""
    plain = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)   # 이미지 제거
    plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", plain)  # 링크는 텍스트만
    plain = re.sub(r"[#*`>\-|]", "", plain)
    plain = re.sub(r"\s+", "", plain)
    return {"chars_no_space": len(plain), "sha256_prefix": __import__("hashlib").sha256(plain.encode()).hexdigest()[:16]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--slug", required=True, help="파일명·이미지 폴더명으로 쓸 영문 slug")
    ap.add_argument("--posts-dir", default="src/content/posts",
                    help="최종 글과 이미지가 놓일 곳")
    ap.add_argument("--work-dir", default=".import-tistory",
                    help="raw.md·meta.json이 놓일 곳. 컬렉션 밖이어야 한다")
    args = ap.parse_args()

    posts = Path(args.posts_dir)
    work = Path(args.work_dir)
    img_dir = posts / args.slug
    img_dir.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)

    html = get(args.url).decode("utf-8", errors="replace")
    body = slice_body(html)
    # 파서와 이미지 수집이 같은 입력을 보도록 여기서 한 번만 걷어낸다.
    body = strip_og_cards(body)
    info = meta_of(html)

    # 이미지를 먼저 내려받는다. 티스토리 CDN URL에는 expires·signature가 붙어
    # 며칠 뒤 만료되므로, HTML을 받은 직후에 저장해두어야 한다.
    urls = image_urls(body)
    rel_paths, saved = [], []
    downloaded_bytes = 0
    for i, u in enumerate(urls, 1):
        try:
            blob = get(u, referer=args.url)
        except Exception as e:  # noqa: BLE001
            print(f"  ! 이미지 {i} 실패: {e}", file=sys.stderr)
            rel_paths.append("")
            continue
        downloaded_bytes += len(blob)
        blob, ext = to_webp(blob, ext_of(u, blob))
        if ext != ".webp":
            # 원본으로 저장해도 글은 정상이지만 레포에 그만큼이 영구히 남는다.
            # 눈에 띄어야 나중에 사람이 판단할 수 있으므로 조용히 넘기지 않는다.
            print(f"  ! 이미지 {i}: WebP 변환 실패 — {ext} 원본으로 저장한다", file=sys.stderr)
        name = f"image-{i}{ext}"
        (img_dir / name).write_bytes(blob)
        rel_paths.append(f"./{args.slug}/{name}")
        saved.append({"file": name, "bytes": len(blob), "source": u.split("?")[0]})

    parser = ToMarkdown(rel_paths)
    parser.feed(body)
    md = parser.result()

    raw_path = work / f"{args.slug}.raw.md"
    raw_path.write_text(md, encoding="utf-8")

    meta = {
        "source_url": args.url,
        "slug": args.slug,
        "title": info["title"],
        "published": info["published"],
        "tags": info["tags"],
        "images": saved,
        "blocks": md.count("\n\n") + 1,
        "fingerprint": fingerprint(md),
    }
    (work / f"{args.slug}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"제목      : {info['title']}")
    print(f"작성일    : {info['published'] or '(찾지 못함)'}")
    print(f"태그      : {', '.join(info['tags']) or '(없음)'}")
    print(f"블록      : {meta['blocks']}개")
    stored_bytes = sum(x["bytes"] for x in saved)
    shrink = f" ({downloaded_bytes // 1024}KB → {stored_bytes // 1024}KB WebP)" if saved else ""
    print(f"이미지    : {len(saved)}/{len(urls)}개 저장{shrink} → {img_dir}/")
    print(f"본문 지문 : {meta['fingerprint']['chars_no_space']}자 / {meta['fingerprint']['sha256_prefix']}")
    print()
    print(f"기계 변환 결과 : {raw_path}   ← 편집하지 마세요 (비교 기준)")
    print(f"메타데이터     : {work / (args.slug + '.meta.json')}")
    print(f"최종 글을 쓸 곳: {posts / (args.slug + '.md')}")


if __name__ == "__main__":
    main()
