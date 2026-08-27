#!/usr/bin/env python3
"""구조화된 마크다운이 원문과 같은 내용인지 확인한다.

fetch_post.py가 만든 .raw.md(기계 변환, 손대지 않은 것)와 사람이 heading을
넣어 완성한 .md를 비교한다. heading·frontmatter를 뺀 나머지가 한 글자라도
다르면 실패로 보고한다.

"구조만 바꾸고 내용은 그대로"라는 약속을 눈으로 확인하는 것은 문단이 수십 개일 때
사실상 불가능하다. 그래서 기계가 대신 본다.

사용:
    python3 verify.py <slug>.raw.md <slug>.md
"""

import argparse
import difflib
import re
import sys
from pathlib import Path


def strip_frontmatter(md: str) -> str:
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            return md[end + 4 :]
    return md


def drop_headings(md: str) -> tuple[str, list[str]]:
    """heading 줄을 걷어낸다. 구조화로 추가가 허용된 유일한 요소다."""
    kept, heads = [], []
    for ln in md.split("\n"):
        if re.match(r"^\s{0,3}#{1,6}\s+\S", ln):
            heads.append(ln.strip())
        else:
            kept.append(ln)
    return "\n".join(kept), heads


def sentences(md: str) -> list[str]:
    """비교 단위. 문장 부호로 끊어 어디가 달라졌는지 짚을 수 있게 한다."""
    text = re.sub(r"!\[[^\]]*\]\(([^)]*)\)", r"[IMG:\1]", md)      # 이미지는 경로만
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)            # 링크는 텍스트만
    text = re.sub(r"```[\s\S]*?```", lambda m: "[CODE]" + re.sub(r"\s+", "", m.group(0)), text)
    text = re.sub(r"[*`>|]|^\s*[-+]\s|^\s*\d+\.\s", "", text, flags=re.M)
    parts = re.split(r"(?<=[.!?。])\s+|\n{2,}", text)
    return [re.sub(r"\s+", "", p) for p in parts if re.sub(r"\s+", "", p)]


def normalize(md: str) -> str:
    return "".join(sentences(md))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path, help="fetch_post.py가 만든 .raw.md")
    ap.add_argument("final", type=Path, help="heading을 넣어 완성한 .md")
    args = ap.parse_args()

    raw = args.raw.read_text(encoding="utf-8")
    final = strip_frontmatter(args.final.read_text(encoding="utf-8"))

    raw_body, raw_heads = drop_headings(raw)
    fin_body, fin_heads = drop_headings(final)

    a, b = normalize(raw_body), normalize(fin_body)

    print(f"원문 글자수(공백·마크업 제외) : {len(a):,}")
    print(f"결과 글자수                    : {len(b):,}")
    print(f"추가된 heading                 : {len(fin_heads) - len(raw_heads)}개")

    # 이미지 순서와 개수
    raw_imgs = re.findall(r"!\[[^\]]*\]\(([^)]*)\)", raw_body)
    fin_imgs = re.findall(r"!\[[^\]]*\]\(([^)]*)\)", fin_body)
    print(f"이미지                         : 원문 {len(raw_imgs)}개 / 결과 {len(fin_imgs)}개", end="")
    print(" (순서 동일)" if raw_imgs == fin_imgs else "  ← 다름!")

    if a == b and raw_imgs == fin_imgs:
        print()
        print("통과 — 내용이 바뀌지 않았습니다. heading만 추가되었습니다.")
        for h in fin_heads:
            print(f"    {h}")
        return

    print()
    print("실패 — 아래 차이를 되돌리세요.")
    sa, sb = sentences(raw_body), sentences(fin_body)
    sm = difflib.SequenceMatcher(None, sa, sb)
    shown = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            continue
        if op in ("delete", "replace"):
            for s in sa[i1:i2]:
                print(f"  - 사라짐 : {s[:90]}")
                shown += 1
        if op in ("insert", "replace"):
            for s in sb[j1:j2]:
                print(f"  + 생김   : {s[:90]}")
                shown += 1
        if shown > 40:
            print("  … (이하 생략)")
            break
    sys.exit(1)


if __name__ == "__main__":
    main()
