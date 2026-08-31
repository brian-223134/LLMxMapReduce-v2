"""Convert a pipeline output survey (.jsonl line) to LaTeX and optionally PDF.

    python scripts/jsonl_to_tex.py \
        --jsonl LLMxMapReduce_V2/output/edge_computing.full.llama33-70b.jsonl \
        --outdir LLMxMapReduce_V2/output/tex [--compile]

Handles the pipeline's markdown dialect: #/##/### headings with numeric
prefixes, **bold**, numeric citation groups [5,7] (mapped to \\cite so the
numbers match the reference list), and the ref_str block "[N] Title URL".
--compile runs pdflatex (tex conda env) twice for stable references.
"""

import argparse
import json
import os
import re
import subprocess

# system MiKTeX. The conda `tex` env's TeX Live is currently unusable —
# mktexfmt dies on a perl @INC path so pdflatex.fmt is never generated.
PDFLATEX = "/usr/local/bin/pdflatex"

TEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def esc(text):
    return "".join(TEX_SPECIAL.get(ch, ch) for ch in text)


def convert_inline(text):
    """Escape TeX specials, then restore citations and bold markup."""
    # stash citation groups before escaping
    cites = []
    def stash(m):
        keys = ",".join(f"ref{n.strip()}" for n in m.group(1).split(","))
        cites.append(f"\\cite{{{keys}}}")
        return f"@@CITE{len(cites) - 1}@@"
    text = re.sub(r"\[([\d, ]+)\]", stash, text)
    text = esc(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    for i, c in enumerate(cites):
        text = text.replace(f"@@CITE{i}@@", c)
    return text


HEADING = {2: "section", 3: "subsection", 4: "subsubsection"}


def convert_body(md):
    out, title = [], None
    for line in md.split("\n"):
        m = re.match(r"^(#+)\s*([\d.]*)\s*(.*)$", line)
        if m:
            level, _num, text = len(m.group(1)), m.group(2), m.group(3).strip()
            if level == 1:          # document title line ("# 0. Topic")
                title = text
                continue
            cmd = HEADING.get(level, "paragraph")
            out.append(f"\\{cmd}{{{convert_inline(text)}}}")
        else:
            out.append(convert_inline(line))
    return title, "\n".join(out)


def convert_refs(ref_str):
    items = []
    for line in ref_str.split("\n"):
        m = re.match(r"^\[(\d+)\]\s+(.*?)\s+(https?://\S+)\s*$", line.strip())
        if not m:
            continue
        n, title, url = m.groups()
        items.append(f"\\bibitem{{ref{n}}} {esc(title)}. \\url{{{url}}}")
    return "\n".join(items), len(items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--compile", action="store_true", help="run pdflatex twice")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    with open(args.jsonl) as f:
        for line in f:
            if not line.strip():
                continue
            d = json.loads(line)
            title, body = convert_body(d["content"])
            title = title or d["title"]
            bib, n_refs = convert_refs(d.get("ref_str", ""))
            tex = f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{url}}
\\usepackage{{parskip}}
\\urlstyle{{same}}
\\title{{{esc(title)}}}
\\author{{LLM$\\times$MapReduce-V2 (meta-llama/llama-3.3-70b-instruct)}}
\\date{{\\today}}
\\begin{{document}}
\\maketitle
\\tableofcontents
\\newpage

{body}

\\begin{{thebibliography}}{{{n_refs}}}
{bib}
\\end{{thebibliography}}
\\end{{document}}
"""
            safe = re.sub(r"[^\w.-]+", "_", d["title"]).strip("_")
            tex_path = os.path.join(args.outdir, f"{safe}.tex")
            with open(tex_path, "w") as out:
                out.write(tex)
            print(f"wrote {tex_path} ({n_refs} refs)")

            if args.compile:
                for _ in range(2):
                    r = subprocess.run(
                        [PDFLATEX, "-interaction=nonstopmode", "-halt-on-error",
                         f"{safe}.tex"],
                        cwd=args.outdir, capture_output=True, text=True)
                if r.returncode != 0:
                    print(r.stdout[-2000:])
                    raise SystemExit(f"pdflatex failed for {tex_path}")
                print(f"compiled {os.path.join(args.outdir, safe + '.pdf')}")


if __name__ == "__main__":
    main()
