# renovdp-midia

Imagens públicas dos posts do Instagram @renato.dodp.
Cada pasta em `posts/` é um post (slides em JPEG 1080x1350 + legenda).

## Como funciona
- `fonte/posts.json`: textos de todos os posts (slides, roteiro dos Reels e legendas).
- `fonte/render.py`: gera as artes em `posts/` e o `calendario.json`.
- `calendario.json`: o que publicar em cada dia útil. Uma tarefa agendada lê este arquivo e publica no Instagram pelo Windsor.

Para mudar um post antes da data: edite `fonte/posts.json`, rode `python3 fonte/render.py <id>` e faça o push.
