"""Convert a pipeline output survey (.jsonl line) to LaTeX and optionally PDF.

    python scripts/jsonl_to_tex.py \
        --jsonl LLMxMapReduce_V2/output/edge_computing.full.llama33-70b.jsonl \
        --outdir LLMxMapReduce_V2/output/tex [--compile]

Handles the pipeline's markdown dialect: #/##/### headings with numeric
prefixes, **bold**, numeric citation groups [5,7] (mapped to \\cite so the
numbers match the reference list), the ref_str block "[N] Title URL" (entries may
wrap over several lines), and FigureModule's <figure-link> placeholders (mermaid
flowchart -> Graphviz figure <title>-figN.pdf, markdown table -> tabular).
--compile runs pdflatex (tex conda env) twice for stable references.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import unicodedata

# system MiKTeX. The conda `tex` env's TeX Live is currently unusable —
# mktexfmt dies on a perl @INC path so pdflatex.fmt is never generated.
PDFLATEX = "/usr/local/bin/pdflatex"
# Graphviz redraws mermaid flowcharts from <figure-link> (None → verbatim fallback)
DOT = shutil.which("dot")

TEX_SPECIAL = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


# pdflatex (no inputenc mapping for Greek) halts on e.g. "PanGu-π" in a
# reference title. Map Greek letters to math symbols; capitals without a
# LaTeX command (Alpha, Beta, ...) look like Latin letters anyway.
_GREEK_CAPS = {"Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma",
               "Upsilon", "Phi", "Psi", "Omega"}


def _greek(ch):
    name = unicodedata.name(ch, "")
    if name == "GREEK SMALL LETTER FINAL SIGMA":
        return "\\ensuremath{\\varsigma}"
    m = re.match(r"GREEK (SMALL|CAPITAL) LETTER (\w+)$", name)
    if not m:
        return None
    # Unicode spells lambda "LAMDA"
    letter = m.group(2).replace("LAMDA", "LAMBDA").capitalize()
    if m.group(1) == "SMALL":
        return "o" if letter == "Omicron" else f"\\ensuremath{{\\{letter.lower()}}}"
    if letter in _GREEK_CAPS:
        return f"\\ensuremath{{\\{letter}}}"
    return unicodedata.lookup(f"LATIN CAPITAL LETTER {letter[0]}")


def esc(text):
    return "".join(TEX_SPECIAL.get(ch) or _greek(ch) or ch for ch in text)


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

# FigureModule (src/decode/figure_module.py) inserts one figure per line as
#   <figure-link title='T' type='mermaid|markdown' content='code with \n escaped'></figure-link>
# which the original web frontend renders. Mermaid flowcharts are redrawn with
# Graphviz, markdown tables become tabulars, anything else is kept verbatim.
FIGURE_LINK = re.compile(r"^\s*<figure-link title='(.*?)' type='(\w+)' content='(.*)'></figure-link>\s*$")
_MM_NODE = r"(\w+)\s*(?:\[\"?(.*?)\"?\]|\(\"?(.*?)\"?\)|\{\"?(.*?)\"?\})?"
_MM_EDGE = r"\s*(?:-->|---|-\.->|==>)\s*(?:\|\"?(.*?)\"?\|\s*)?"
_MM_RANKDIR = {"LR": "LR", "RL": "RL", "TD": "TB", "TB": "TB", "BT": "BT"}


def mermaid_to_dot(code):
    """`graph|flowchart <dir>` + node/edge lines → DOT source, None if unsupported."""
    lines = [l.strip() for l in code.strip().split("\n") if l.strip() and not l.strip().startswith("%%")]
    m = re.match(r"^(?:graph|flowchart)\s+(\w+)\s*;?$", lines[0]) if lines else None
    if not m or m.group(1) not in _MM_RANKDIR:
        return None
    labels, edges = {}, []
    for line in lines[1:]:
        line = line.rstrip(";")
        parts = re.split(_MM_EDGE, line)       # node, edge label, node, edge label, node ...
        nodes = parts[0::2]
        if not all(re.fullmatch(_MM_NODE, p.strip()) for p in nodes):
            return None
        ids = []
        for p in nodes:
            nm = re.fullmatch(_MM_NODE, p.strip())
            ids.append(nm.group(1))
            label = next((g for g in nm.groups()[1:] if g is not None), None)
            if label is not None or nm.group(1) not in labels:
                labels[nm.group(1)] = label if label is not None else nm.group(1)
        for a, lab, b in zip(ids, parts[1::2], ids[1:]):
            edges.append((a, b, lab))
    q = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    out = [f"digraph G {{ rankdir={_MM_RANKDIR[m.group(1)]};",
           '  node [shape=box, style=rounded, fontname="Helvetica", fontsize=11];',
           '  edge [fontname="Helvetica", fontsize=9];']
    out += [f"  {q(k)} [label={q(v)}];" for k, v in labels.items()]
    out += [f"  {q(a)} -> {q(b)}" + (f" [label={q(lab)}]" if lab else "") + ";" for a, b, lab in edges]
    return "\n".join(out + ["}"])


def markdown_table_to_tex(code):
    rows = [l.strip() for l in code.strip().split("\n") if l.strip()]
    if len(rows) < 2 or not all(r.startswith("|") for r in rows):
        return None
    cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows
             if not re.fullmatch(r"\|[\s:|-]+\|", r)]
    ncol = max(len(r) for r in cells)
    col = f">{{\\raggedright\\arraybackslash}}p{{\\dimexpr{1 / ncol:.3f}\\linewidth-2\\tabcolsep\\relax}}"
    body = [" & ".join(convert_inline(c) for c in r + [""] * (ncol - len(r))) + r" \\" for r in cells]
    return "\n".join([f"\\begin{{tabular}}{{@{{}}{col * ncol}@{{}}}}", r"\toprule", body[0], r"\midrule",
                      *body[1:], r"\bottomrule", r"\end{tabular}"])


def convert_figure(title, kind, code, fig_dir, stem):
    """→ LaTeX block for one <figure-link>. Mermaid PDFs are written to fig_dir."""
    code = code.replace("\\n", "\n")
    if kind == "markdown":
        table = markdown_table_to_tex(code)
        if table:
            return "\n".join([r"\begin{table}[htbp]", r"\centering", f"\\caption{{{convert_inline(title)}}}",
                              table, r"\end{table}"])
    if kind == "mermaid":
        dot = mermaid_to_dot(code)
        if dot and DOT:
            with open(os.path.join(fig_dir, f"{stem}.dot"), "w") as f:
                f.write(dot + "\n")
            r = subprocess.run([DOT, "-Tpdf", "-o", f"{stem}.pdf", f"{stem}.dot"],
                               cwd=fig_dir, capture_output=True, text=True)
            if r.returncode == 0:
                return "\n".join([r"\begin{figure}[htbp]", r"\centering",
                                  f"\\includegraphics[width=\\linewidth,height=0.4\\textheight,keepaspectratio]{{{stem}.pdf}}",
                                  f"\\caption{{{convert_inline(title)}}}", r"\end{figure}"])
            print(f"dot failed for {stem}: {r.stderr.strip()[:200]}")
    # unsupported diagram type / unparsable table: keep the source readable
    return "\n".join([r"\begin{figure}[htbp]", r"\begin{verbatim}", code.strip(), r"\end{verbatim}",
                      f"\\caption{{{convert_inline(title)}}}", r"\end{figure}"])


def convert_body(md, fig_dir=".", stem="fig"):
    out, title, n_fig = [], None, 0
    for line in md.split("\n"):
        f = FIGURE_LINK.match(line)
        if f:
            n_fig += 1
            out.append(convert_figure(*f.groups(), fig_dir, f"{stem}-fig{n_fig}"))
            continue
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
    # titles copied from arXiv metadata keep their line wraps, so one entry can
    # span several lines: join continuation lines onto the preceding "[N]" line.
    entries = []
    for line in ref_str.split("\n"):
        if re.match(r"^\s*\[\d+\]", line) or not entries:
            entries.append(line.strip())
        elif line.strip():
            entries[-1] += " " + line.strip()
    items = []
    for entry in entries:
        m = re.match(r"^\[(\d+)\]\s+(.*?)\s+(https?://\S+)\s*$", " ".join(entry.split()))
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
            safe = re.sub(r"[^\w.-]+", "_", d["title"]).strip("_")
            title, body = convert_body(d["content"], args.outdir, safe)
            title = title or d["title"]
            bib, n_refs = convert_refs(d.get("ref_str", ""))
            tex = f"""\\documentclass[11pt]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage[hidelinks]{{hyperref}}
\\usepackage{{url}}
\\usepackage{{parskip}}
\\usepackage{{graphicx}}
\\usepackage{{booktabs}}
\\usepackage{{array}}
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
