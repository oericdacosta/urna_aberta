"""CLI: inventário das fontes habilitadas. Uso: python -m urna_aberta.discover"""

import argparse
import sys
from pathlib import Path

import httpx

from urna_aberta.ckan import CkanError, head, package_resources
from urna_aberta.config import load_election


def _fmt_size(n: int | None) -> str:
    return "?" if n is None else f"{n} ({n / 1_048_576:.1f} MiB)"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="urna_aberta.discover")
    ap.add_argument("--config", type=Path, default=Path("config/elections/2026.yaml"))
    ap.add_argument("--out", type=Path, default=Path("docs/fontes.md"))
    args = ap.parse_args(argv)

    cfg = load_election(args.config)
    lines = [
        f"# Fontes de dados {cfg.ano}",
        "",
        "Gerado por `python -m urna_aberta.discover`. Tamanhos via HEAD no CDN.",
    ]
    errors = 0
    with httpx.Client(timeout=30) as client:
        for ds in (d for d in cfg.datasets if d.enabled):
            lines += ["", f"## {ds.id}", ""]
            try:
                resources = package_resources(client, ds.id)
            except CkanError as e:
                errors += 1
                lines.append(f"AUSENTE: {e}")
                continue
            lines += [
                "| Nome | Formato | URL | Bytes | Modificado | ETag |",
                "|---|---|---|---|---|---|",
            ]
            for r in resources:
                try:
                    h = head(client, r.url)
                    size, mod, etag = (
                        _fmt_size(h.size),
                        h.last_modified or r.last_modified,
                        h.etag,
                    )
                except httpx.HTTPError as e:
                    errors += 1
                    size, mod, etag = f"ERRO {e}", r.last_modified, None
                name = r.name.replace("|", "/")
                cells = [name, r.format, r.url, size, mod or "?", etag or ""]
                lines.append("| " + " | ".join(cells) + " |")
    text = "\n".join(lines) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, "utf-8")
    print(text)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
