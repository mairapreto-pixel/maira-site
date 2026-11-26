#!/usr/bin/env python3
"""Gera o site da Maíra Preto a partir de conteudo/*.json.

Uso:
  python3 build.py                 site final em ./site (endereços limpos: /projects/slug)
  python3 build.py --previa DIR    prévia local: links .html relativos e fotos de DIR/<id>.jpg
"""
import html, json, os, re, shutil, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
SAIDA = RAIZ / "site"
FOTOS = RAIZ / "fotos"
LARGURAS = [640, 1024, 1600, 2400]
# Prefixo dos endereços: "/" no domínio próprio; "/maira-site/" no endereço provisório do GitHub.
BASE = "/" + os.environ.get("BASE", "/").strip("/") + "/" if os.environ.get("BASE", "/").strip("/") else "/"

args = sys.argv[1:]
PREVIA = None
if "--previa" in args:
    PREVIA = Path(args[args.index("--previa") + 1]).resolve()

S = json.loads((RAIZ / "conteudo/site.json").read_text())
TODOS = json.loads((RAIZ / "conteudo/projetos.json").read_text())
P = [p for p in TODOS if p.get("publicado", True)]  # só os marcados "publicado": true entram no site
POR_SLUG = {p["slug"]: p for p in P}

META_FOTO = {}
for p in P:
    for f in p["fotos"]:
        META_FOTO[f["id"]] = {**f, "alt": p["titulo"]}
for k, v in S["fotos_paginas"].items():
    META_FOTO[k] = {"id": k, **v}

e = lambda t: html.escape(str(t), quote=True)


def nome_curto(p):
    return re.sub(r"^(Casamento|Editorial) ", "", p["titulo"])


def local(p):
    for k, v in p["ficha"]:
        if k.lower() in ("local", "espaço"):
            return re.sub(r"\s*\(.*?\)", "", v).split(",")[0].strip()
    return ""


# ---------- endereços ----------
class Pag:
    def __init__(self, arquivo, url):
        self.arquivo, self.url = arquivo, url  # arquivo: 'projects/x.html'; url: '/projects/x'

    def rel(self):
        return "../" * self.arquivo.count("/")


def link(atual, destino_arquivo, destino_url, ancora=""):
    if PREVIA:
        return atual.rel() + destino_arquivo + ancora
    return BASE.rstrip("/") + destino_url + ancora


def L(atual, nome, extra=""):
    mapa = {
        "home": ("index.html", "/"),
        "projetos": ("projects.html", "/projects"),
        "sobre": ("about.html", "/about"),
        "contato": ("contact.html", "/contact"),
    }
    if nome.startswith("p:"):
        slug = nome[2:]
        return link(atual, f"projects/{slug}.html", f"/projects/{slug}")
    a, u = mapa[nome]
    if extra:
        return (atual.rel() + a + extra) if PREVIA else (BASE.rstrip('/') + u + extra)
    return link(atual, a, u)


def ativo(atual, nome):
    return ' aria-current="page"' if atual.url.rstrip("/") == {"projetos": "/projects", "sobre": "/about", "contato": "/contact"}[nome] or (nome == "projetos" and atual.url.startswith("/projects/")) else ""


def asset(atual, caminho):
    return (atual.rel() if PREVIA else BASE) + caminho


# ---------- fotos ----------
copiadas = set()


def foto(atual, fid, classe="foto", sizes="100vw", eager=False, alt=None, pos=None):
    m = META_FOTO.get(fid, {"w": 4, "h": 5, "alt": ""})
    alt = m.get("alt", "") if alt is None else alt
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    estilo = f' style="object-position:{pos}"' if pos else ""
    disp = [w for w in LARGURAS if w <= m["w"]] or [LARGURAS[0]]
    if (FOTOS / f"{fid}-{disp[-1]}.webp").exists():
        srcset = ", ".join(f'{asset(atual, f"fotos/{fid}-{w}.webp")} {w}w' for w in disp)
        src = asset(atual, f"fotos/{fid}-{disp[min(2, len(disp)-1)]}.webp")
        img = f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" width="{m["w"]}" height="{m["h"]}" alt="{e(alt)}" {load}{estilo}>'
    elif PREVIA and (PREVIA / f"{fid}.jpg").exists():
        if fid not in copiadas:
            (SAIDA / "fotos-previa").mkdir(parents=True, exist_ok=True)
            shutil.copy(PREVIA / f"{fid}.jpg", SAIDA / "fotos-previa" / f"{fid}.jpg")
            copiadas.add(fid)
        img = f'<img src="{asset(atual, f"fotos-previa/{fid}.jpg")}" width="{m["w"]}" height="{m["h"]}" alt="{e(alt)}" {load}{estilo}>'
    else:
        return f'<div class="{classe} vazia" role="img" aria-label="{e(alt)}">foto</div>'
    return f'<div class="{classe}">{img}</div>'


def og_imagem(fid):
    return f'{S["dominio"]}/fotos/{fid}-1600.jpg'


# ---------- moldura ----------
def wa_link():
    from urllib.parse import quote
    return f'https://wa.me/{S["whatsapp_numero"]}?text={quote(S["whatsapp_mensagem"])}'


def pagina(atual, titulo, descricao, corpo, og=None, extra_head=""):
    og = og or S["home"]["abertura"]["cena"]
    canon = S["dominio"] + (atual.url if atual.url != "/" else "/")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{e(canon)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Maíra Preto">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:url" content="{e(canon)}">
<meta property="og:image" content="{e(og_imagem(og))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FBF8F2">
<link rel="icon" type="image/png" href="{asset(atual, 'favicon.png')}">
<link rel="apple-touch-icon" href="{asset(atual, 'apple-touch-icon.png')}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500&family=Geist+Mono:wght@500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{asset(atual, 'estilo.css')}">
{extra_head}</head>
<body>
<a class="pular" href="#conteudo">Pular para o conteúdo</a>
<header class="wrap topo">
  <a class="logo" href="{L(atual, 'home')}" aria-label="Maíra Preto, início"><img src="{asset(atual, 'logo-mp-512.png')}" width="512" height="512" alt="Maíra Preto"></a>
  <nav aria-label="Principal" class="mono">
    <a href="{L(atual, 'projetos')}"{ativo(atual, 'projetos')}>Projetos</a>
    <a href="{L(atual, 'sobre')}"{ativo(atual, 'sobre')}>Sobre</a>
    <a class="botao" href="{L(atual, 'contato')}"{ativo(atual, 'contato')}>Contato</a>
  </nav>
</header>
<main id="conteudo">
{corpo}
</main>
<footer class="wrap mono rodape">
  <span>{e(S['local'])}</span>
  <div class="links">
    <a href="{wa_link()}" target="_blank" rel="noopener">WhatsApp</a>
    <a href="mailto:{S['email']}" class="minusculo">{S['email']}</a>
    <a href="{S['instagram']}" target="_blank" rel="noopener">Instagram</a>
    <a href="{S['linkedin']}" target="_blank" rel="noopener">LinkedIn</a>
    <a href="{S['revista_nou']}" target="_blank" rel="noopener">Revista NOU</a>
  </div>
  <span>© 2026 Maíra Preto</span>
</footer>
</body>
</html>
"""


def faixa_contato(atual):
    c = S["contato"]
    return f"""<section class="faixa">
  <div class="dentro">
    <h2 class="disp">{e(c['titulo'])}</h2>
    <div class="acoes">
      <a class="botao cheio grande" href="{wa_link()}" target="_blank" rel="noopener">Consultar disponibilidade</a>
      <a class="botao grande minusculo" href="mailto:{S['email']}">{S['email']}</a>
    </div>
  </div>
</section>"""


def card(atual, p, fid, sizes):
    return f"""<a class="card" href="{L(atual, 'p:' + p['slug'])}" data-cat="{e(p['categoria'])}">
        {foto(atual, fid, sizes=sizes, alt=f"{p['titulo']}")}
        <div class="legenda"><span class="nome">{e(nome_curto(p))}</span><span class="cat mono">{e(p['categoria'])}</span></div>
      </a>"""


# ---------- páginas ----------
def home():
    a = Pag("index.html", "/")
    h = S["home"]
    l1 = "\n      ".join(card(a, POR_SLUG[d["projeto"]], d["foto"], "(max-width:760px) 50vw, 33vw") for d in h["destaques_linha1"])
    l2 = "\n      ".join(card(a, POR_SLUG[d["projeto"]], d["foto"], "(max-width:760px) 100vw, 50vw") for d in h["destaques_linha2"])
    serv = "\n".join(f"""  <a class="servico" href="{L(a, 'projetos', '?category=' + s['link'])}">
    <span class="nome">{e(s['nome'])}</span>
    <span class="texto">{e(s['texto'])}</span>
    <span class="ir mono">Ver {e(s['nome'].lower())} →</span>
  </a>""" for s in h["servicos"])
    ld = json.dumps({"@context": "https://schema.org", "@type": "ProfessionalService", "name": "Maíra Preto · Fotografia & Direção de Arte",
                     "url": S["dominio"], "email": S["email"], "telephone": "+" + S["whatsapp_numero"],
                     "areaServed": "São Paulo, Brasil e internacional", "sameAs": [S["instagram"], S["linkedin"]]}, ensure_ascii=False)
    corpo = f"""<section class="wrap">
  <div class="abertura">
    {foto(a, h['abertura']['cena'], 'foto cena', '(max-width:760px) 66vw, 75vw', eager=True, alt='Noiva no carro, em preto e branco. Casamento Ana e Gabriel', pos='30% 40%')}
    {foto(a, h['abertura']['detalhe'], sizes='(max-width:760px) 34vw, 25vw', eager=True, alt='Detalhe do buquê de copos-de-leite')}
  </div>
  <div class="abertura-legenda mono"><span>{e(S['nome'])} · {e(S['assinatura'])}</span><span class="esconde-cel">São Paulo · Worldwide</span></div>
</section>

<section class="wrap">
  <div class="lema">
    <h1 class="disp">Tempo,<br>Luz e Presença.</h1>
    <p>{e(h['frase'])}</p>
  </div>
</section>

<section class="wrap" aria-labelledby="t-projetos">
  <div class="cabeca">
    <h2 class="disp titulo-secao" id="t-projetos">Projetos</h2>
    <a class="mono sublinha" style="font-size:13px" href="{L(a, 'projetos')}">Ver todos os projetos</a>
  </div>
  <div class="g3">
      {l1}
  </div>
  <div class="g2">
      {l2}
  </div>
</section>

<section class="wrap servicos" aria-labelledby="t-servicos">
  <div class="cabeca-s"><h2 class="disp titulo-secao" id="t-servicos">Um olhar, diferentes momentos</h2></div>
{serv}
</section>

<section class="wrap">
  <div class="sobre-curto">
    {foto(a, h['sobre_foto'], sizes='(max-width:760px) 100vw, 380px', alt='Maíra Preto fotografando')}
    <div class="txt">
      <span class="mono sub" style="font-size:12px">{e(S['nome'])} · {e(S['assinatura'])}</span>
      <p class="disp frase">{e(h['sobre_frase'])}</p>
      <p class="sub" style="font-size:15px">Fundadora e diretora criativa da <a class="sublinha" style="color:var(--tinta)" href="{S['revista_nou']}" target="_blank" rel="noopener">Revista NOU</a>.</p>
      <a class="botao" style="align-self:flex-start" href="{L(a, 'sobre')}">Sobre a Maíra</a>
    </div>
  </div>
</section>

{faixa_contato(a)}"""
    return a, pagina(a, "Maíra Preto · Fotografia & Direção de Arte", S["descricao_google"], corpo,
                     extra_head=f'<script type="application/ld+json">{ld}</script>\n')


def projetos():
    a = Pag("projects.html", "/projects")
    cats = S["projetos_pagina"]["categorias"]
    botoes = '<button class="botao ativo" type="button" data-filtro="" aria-pressed="true">Todos</button>' + "".join(
        f'<button class="botao" type="button" data-filtro="{e(c)}" aria-pressed="false">{e(c)}</button>' for c in cats)
    cards = "\n    ".join(card(a, p, p["fotos"][0]["id"], "(max-width:520px) 100vw, (max-width:900px) 50vw, 33vw") for p in P)
    js = """<script>
(function(){
  var bs=document.querySelectorAll('[data-filtro]'),cs=document.querySelectorAll('.lista .card');
  function aplica(c){
    bs.forEach(function(b){var on=b.getAttribute('data-filtro')===c;b.classList.toggle('ativo',on);b.setAttribute('aria-pressed',on)});
    cs.forEach(function(k){k.hidden=!!c&&k.getAttribute('data-cat')!==c});
  }
  bs.forEach(function(b){b.addEventListener('click',function(){var c=b.getAttribute('data-filtro');aplica(c);
    try{var u=new URL(location.href);c?u.searchParams.set('category',c):u.searchParams.delete('category');history.replaceState(null,'',u)}catch(e){}})});
  try{var c=new URL(location.href).searchParams.get('category');if(c)aplica(c)}catch(e){}
})();
</script>"""
    corpo = f"""<section class="wrap abre">
  <h1 class="disp">Projetos</h1>
  <p class="sub">{e(S['projetos_pagina']['subtitulo'])}</p>
</section>
<section class="wrap">
  <div class="filtros mono" role="group" aria-label="Filtrar por categoria">{botoes}</div>
  <div class="lista">
    {cards}
  </div>
</section>
{faixa_contato(a)}
{js}"""
    return a, pagina(a, "Projetos · Maíra Preto", "Casamentos, festas e atmosferas fotografados por Maíra Preto.", corpo)


def fileiras(atual, fotos):
    """Horizontal ocupa a largura; duas verticais seguidas viram um par; vertical sozinha fica centralizada."""
    out, i = [], 0
    while i < len(fotos):
        f = fotos[i]
        if f["w"] > f["h"]:
            out.append(f'<div class="fileira larga">{foto(atual, f["id"], sizes="100vw")}</div>')
            i += 1
        elif i + 1 < len(fotos) and fotos[i + 1]["w"] <= fotos[i + 1]["h"]:
            out.append(f'<div class="fileira par">{foto(atual, f["id"], sizes="50vw")}{foto(atual, fotos[i+1]["id"], sizes="50vw")}</div>')
            i += 2
        else:
            out.append(f'<div class="fileira so">{foto(atual, f["id"], sizes="(max-width:760px) 100vw, 640px")}</div>')
            i += 1
    return out


def projeto(p, prox):
    a = Pag(f"projects/{p['slug']}.html", f"/projects/{p['slug']}")
    rows = fileiras(a, p["fotos"])
    primeira, resto = rows[0], rows[1:]
    primeira = primeira.replace('loading="lazy" decoding="async"', 'fetchpriority="high"')
    dados = [("Projeto", nome_curto(p)), ("Categoria", p["categoria"]), ("Ano", p["ano"]), ("Cliente", p["cliente"])]
    dl = "".join(f'<div><dt class="mono">{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in dados if v)
    ficha = "".join(f'<div><dt class="mono">{e(k)}</dt><dd>{e(v)}</dd></div>' for k, v in p["ficha"])
    texto = f'<p class="texto-projeto">{e(p["texto"])}</p>' if p.get("texto") else ""
    pf = prox["fotos"]
    vert = next((f for f in pf if f["h"] > f["w"]), pf[0])
    hor = next((f for f in pf if f["w"] > f["h"]), pf[-1])
    corpo = f"""<section class="wrap abre projeto-abre">
  <div class="trilha mono"><a href="{L(a, 'projetos')}">Projetos</a> / <a href="{L(a, 'projetos', '?category=' + p['categoria'])}">{e(p['categoria'])}</a></div>
  <h1 class="disp">{e(p['frase'])}</h1>
</section>
<section class="wrap">
  {primeira}
  <dl class="dados">{dl}</dl>
  {texto}
  <div class="sequencia">
    {chr(10).join('    ' + r for r in resto)}
  </div>
</section>
<section class="wrap ficha">
  <div class="linha"></div>
  <h2 class="disp titulo-secao" style="font-size:clamp(32px,3.4vw,48px)">Ficha técnica</h2>
  <dl>{ficha}</dl>
</section>
<section class="wrap proximo">
  <div class="cabeca">
    <span class="mono sub" style="font-size:13px">Próximo projeto</span>
    <a class="mono sublinha" style="font-size:13px" href="{L(a, 'projetos')}">Ver todos os projetos</a>
  </div>
  <a class="card" href="{L(a, 'p:' + prox['slug'])}">
    <div class="fotos">{foto(a, vert['id'], sizes='40vw', alt=prox['titulo'])}{foto(a, hor['id'], sizes='60vw', alt=prox['titulo'])}</div>
    <div class="legenda"><span class="nome">{e(nome_curto(prox))}</span><span class="cat mono">{e(prox['categoria'])}{(' · ' + e(local(prox))) if local(prox) else ''}</span></div>
  </a>
</section>
{faixa_contato(a)}"""
    return a, pagina(a, f"{p['titulo']} · Maíra Preto", p["descricao_google"], corpo, og=p["fotos"][0]["id"])


def sobre():
    a = Pag("about.html", "/about")
    s = S["sobre"]
    blocos = []
    for i, sec in enumerate(s["secoes"]):
        if "itens" in sec:
            corpo = '<div class="itens">' + "".join(f'<div><div class="nome">{e(n)}</div><div class="papel mono">{e(r)}</div></div>' for n, r in sec["itens"]) + "</div>"
        else:
            ps = sec["paragrafos"]
            corpo = "".join(f"<p>{e(t)}</p>" for t in ps[:-1] if True) if sec["titulo"].startswith("Projeto") else "".join(f"<p>{e(t)}</p>" for t in ps)
            if sec["titulo"].startswith("Projeto"):
                corpo += f'<p class="citacao">{e(ps[-1])}</p><a class="botao" style="align-self:flex-start" href="{S["revista_nou"]}" target="_blank" rel="noopener">Conhecer a Revista NOU</a>'
        blocos.append(f'<section class="wrap bloco"><h2 class="disp">{e(sec["titulo"])}</h2><div class="corpo">{corpo}</div></section>')
        if i == 1:
            blocos.append(f'<section class="wrap"><div class="dupla">{foto(a, s["retrato"], sizes="40vw", alt="Maíra Preto fotografando")}{foto(a, s["fotos_extra"][1], sizes="60vw")}</div></section>')
    corpo = f"""<section class="wrap sobre-abre">
  <div class="mono sub" style="font-size:12px;margin-bottom:20px">Sobre</div>
  <h1 class="disp">{e(s['titulo'])}</h1>
</section>
<section class="wrap">{foto(a, s['foto_abertura'], 'foto largura-total', '100vw', eager=True)}</section>
{chr(10).join(blocos)}
{faixa_contato(a)}"""
    return a, pagina(a, "Sobre · Maíra Preto", "Maíra Preto atua entre fotografia, direção de arte e projetos editoriais, e é fundadora e diretora criativa da Revista NOU.", corpo, og=s["foto_abertura"])


def contato():
    a = Pag("contact.html", "/contact")
    c = S["contato"]
    itens = [("E-mail", f'<a class="sublinha" href="mailto:{S["email"]}">{S["email"]}</a>'),
             ("WhatsApp", f'<a class="sublinha" href="{wa_link()}" target="_blank" rel="noopener">{S["whatsapp_exibido"]}</a>'),
             ("Instagram", f'<a class="sublinha" href="{S["instagram"]}" target="_blank" rel="noopener">@mairapretophoto</a>'),
             ("Atendimento", e(S["local"]))]
    lista = "".join(f'<div class="item"><span class="rot mono">{k}</span><span class="val">{v}</span></div>' for k, v in itens)
    corpo = f"""<section class="wrap contato">
  <div>
    <div class="mono sub" style="font-size:12px;margin-bottom:20px">Contato</div>
    <h1 class="disp">{e(S['lema'])}</h1>
    <p class="sub" style="margin-top:28px;font-size:17px;max-width:520px">{e(c['texto'])}</p>
    <div class="acoes" style="margin-top:28px"><a class="botao cheio grande" href="{wa_link()}" target="_blank" rel="noopener">Consultar disponibilidade</a></div>
    <div class="lista-contato">{lista}</div>
  </div>
  {foto(a, c['foto'], sizes='(max-width:760px) 100vw, 40vw', eager=True)}
</section>
<div style="height:var(--secao)"></div>"""
    return a, pagina(a, "Contato · Maíra Preto", "Fale com Maíra Preto sobre casamentos, festas e projetos de marca. São Paulo e internacional.", corpo, og=c["foto"])


def nao_encontrada():
    a = Pag("404.html", "/404")
    corpo = f"""<section class="wrap abre" style="min-height:50vh">
  <h1 class="disp">Página não encontrada.</h1>
  <p class="sub">O endereço pode ter mudado. <a class="sublinha" style="color:var(--tinta)" href="{L(a, 'projetos')}">Ver os projetos</a> ou <a class="sublinha" style="color:var(--tinta)" href="{L(a, 'home')}">voltar ao início</a>.</p>
</section>"""
    return a, pagina(a, "Página não encontrada · Maíra Preto", S["descricao_google"], corpo)


# ---------- gerar ----------
def main():
    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    SAIDA.mkdir()
    for f in (RAIZ / "estatico").iterdir():
        shutil.copy(f, SAIDA / f.name)
    if FOTOS.exists() and not PREVIA:
        shutil.copytree(FOTOS, SAIDA / "fotos")
    elif FOTOS.exists() and PREVIA:
        shutil.copytree(FOTOS, SAIDA / "fotos")
    paginas = [home(), projetos(), sobre(), contato(), nao_encontrada()]
    for i, p in enumerate(P):
        paginas.append(projeto(p, P[(i + 1) % len(P)]))
    for pag, conteudo in paginas:
        destino = SAIDA / pag.arquivo
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(conteudo)
        if not PREVIA and pag.arquivo == "projects.html":
            (SAIDA / "projects").mkdir(exist_ok=True)
            (SAIDA / "projects" / "index.html").write_text(conteudo.replace('href="/estilo.css"', 'href="/estilo.css"'))
    if not PREVIA:
        urls = ["/", "/projects", "/about", "/contact"] + [f"/projects/{p['slug']}" for p in P]
        (SAIDA / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
            "".join(f"  <url><loc>{S['dominio']}{u}</loc></url>\n" for u in urls) + "</urlset>\n")
        (SAIDA / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {S['dominio']}/sitemap.xml\n")
        (SAIDA / "CNAME").write_text(S["dominio"].replace("https://", "") + "\n")
        (SAIDA / ".nojekyll").write_text("")
    faltam = sorted({fid for fid in META_FOTO if not (FOTOS / f"{fid}-640.webp").exists()})
    print(f"{len(paginas)} páginas em {SAIDA}. Fotos ainda não baixadas: {len(faltam)}")


if __name__ == "__main__":
    main()
