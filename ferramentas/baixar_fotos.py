#!/usr/bin/env python3
"""Baixa os originais das fotos do Framer (uma vez só) e gera as versões do site.

Para cada foto citada em conteudo/*.json gera em fotos/:
  <id>-640.webp, -1024.webp, -1600.webp, -2400.webp  (o navegador escolhe a do tamanho da tela)
  <id>-1600.jpg                                     (prévia ao compartilhar o link)
Fotos que já existem em fotos/ são puladas. Originais ficam em originais/ (fora do site).

Para trocar ou acrescentar uma foto sem o Framer: coloque o arquivo em originais/<nome>.jpg,
cite <nome> no conteudo e rode este script de novo.
"""
import json, sys, time, urllib.request
from pathlib import Path
from PIL import Image, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
ORIG = RAIZ / "originais"
FOTOS = RAIZ / "fotos"
LARGURAS = [640, 1024, 1600, 2400]
ORIG.mkdir(exist_ok=True)
FOTOS.mkdir(exist_ok=True)

S = json.loads((RAIZ / "conteudo/site.json").read_text())
P = json.loads((RAIZ / "conteudo/projetos.json").read_text())
lista = {f["id"]: f["ext"] for p in P if p.get("publicado", True) for f in p["fotos"]}
lista.update({k: v["ext"] for k, v in S["fotos_paginas"].items()})


def baixar(fid, ext):
    destino = ORIG / f"{fid}.{ext}"
    if destino.exists():
        return destino
    for tentativa in range(3):
        try:
            req = urllib.request.Request(f"https://framerusercontent.com/images/{fid}.{ext}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                destino.write_bytes(r.read())
            return destino
        except Exception as erro:
            print(f"  tentativa {tentativa + 1} falhou para {fid}: {erro}")
            time.sleep(3)
    return None


def gerar(fid, origem):
    im = ImageOps.exif_transpose(Image.open(origem))
    icc = im.info.get("icc_profile")
    im = im.convert("RGB")
    for w in LARGURAS:
        if w > im.width and w != LARGURAS[0]:
            continue
        alvo = FOTOS / f"{fid}-{w}.webp"
        if alvo.exists():
            continue
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(alvo, "WEBP", quality=84, method=6, icc_profile=icc)
    jpg = FOTOS / f"{fid}-1600.jpg"
    if not jpg.exists():
        w = min(1600, im.width)
        im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(jpg, "JPEG", quality=86, optimize=True, progressive=True, icc_profile=icc)


falhas = []
for i, (fid, ext) in enumerate(lista.items(), 1):
    if (FOTOS / f"{fid}-640.webp").exists() and (FOTOS / f"{fid}-1600.jpg").exists():
        continue
    print(f"[{i}/{len(lista)}] {fid}")
    origem = next(iter(ORIG.glob(f"{fid}.*")), None) or baixar(fid, ext)
    if not origem:
        falhas.append(fid)
        continue
    gerar(fid, origem)

print(f"Pronto. {len(lista) - len(falhas)} fotos ok, {len(falhas)} com falha.")
if falhas:
    print("Falharam:", ", ".join(falhas))
    sys.exit(1)
