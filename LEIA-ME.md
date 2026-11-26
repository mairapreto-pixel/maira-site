# Site Maíra Preto · Fotografia & Direção de Arte

Site em código, sem Framer. Hospedagem gratuita no GitHub Pages, com o domínio mairapreto.com.br.

## Como está organizado

- `conteudo/projetos.json`: os projetos (título, frase, categoria, ano, cliente, ficha técnica, fotos). A ordem do arquivo é a ordem do site.
- `conteudo/site.json`: textos da home, Sobre, Contato, contatos e as fotos escolhidas para a home.
- `estatico/estilo.css`: o visual (cores, fontes, espaçamentos, celular).
- `build.py`: gera as páginas em `site/`.
- `ferramentas/baixar_fotos.py`: baixa os originais das fotos do Framer uma única vez e gera as versões leves (640, 1024, 1600 e 2400 px, em WebP) que o navegador escolhe pelo tamanho da tela.
- `.github/workflows/publicar.yml`: a cada alteração, baixa as fotos que faltam, gera o site e publica.

Os endereços são os mesmos do site atual (`/projects/casamento-ana-e-gabriel`, `/about`, `/contact`, `/projects?category=Casamentos`), então links antigos e o Google continuam funcionando.

## Publicar (uma vez só)

1. No GitHub (conta mairapreto-pixel), criar um repositório chamado `maira-site`. Pode ser público: é o próprio site.
2. Enviar estes arquivos para o repositório (ou dar acesso ao Claude para enviar).
3. Em **Settings → Pages**, em *Source*, escolher **GitHub Actions**.
4. Em **Actions → Publicar o site → Run workflow**. Na primeira vez ele baixa as 96 fotos originais do Framer e as guarda no repositório. A partir daí o site não depende mais do Framer.
5. Testar num endereço provisório: em **Settings → Pages → Custom domain**, colocar `novo.mairapreto.com.br` e, no painel do domínio (registro.br ou onde estiver o DNS), criar um registro **CNAME** `novo` → `mairapreto-pixel.github.io`.
6. Aprovado o teste, trocar para o domínio principal:
   - no DNS, apontar `mairapreto.com.br` (registros **A**) para `185.199.108.153`, `185.199.109.153`, `185.199.110.153` e `185.199.111.153`, e `www` (**CNAME**) para `mairapreto-pixel.github.io`;
   - em Settings → Pages, mudar o Custom domain para `mairapreto.com.br` e marcar **Enforce HTTPS**.
7. Só depois de conferir o site no ar, cancelar o plano do Framer.

## Atualizar

- Novo projeto: acrescentar um bloco em `conteudo/projetos.json` e colocar as fotos em `originais/` (ou usar fotos já no Framer enquanto ele existir). Ao salvar no GitHub, o site se atualiza sozinho em poucos minutos.
- Trocar texto: editar `conteudo/site.json` ou `conteudo/projetos.json` direto no GitHub.

## Prévia no computador

`python3 build.py` gera o site em `site/`. Com as fotos já baixadas em `fotos/`, basta abrir `site/index.html` por um servidor local (`python3 -m http.server -d site`).
