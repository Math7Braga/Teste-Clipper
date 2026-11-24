# Clipper do GTA 6

Baseada no [Clipper do GTA 6 original](https://github.com/davixavier-coder/skill-clips), com o modo "trecho" (cortar um pedaço escolhido, inclusive de live ao vivo com DVR).

Uma skill grátis pro Claude Code que transforma lives longas de streamers em cortes verticais prontos pra postar.

Você manda o link de uma live (YouTube, Twitch ou Kick), ou pede as maiores lives de GTA 6 do dia, e recebe:

- o corte vertical (1080×1920): câmera do streamer em cima, jogo embaixo
- título de gancho e legenda palavra por palavra
- um `.txt` com a legenda do post, as hashtags e o crédito da live
- a thumbnail de cada corte: `thumb_NN.jpg` (YouTube, 1280×720) e `capa_NN.jpg` (Shorts/Reels/TikTok, 1080×1920)

## O que ela faz, em 4 passos

1. **Baixa só o áudio.** Uma live de 4 horas fica com algumas centenas de MB, não um vídeo gigante.
2. **Escuta a live inteira no seu computador.** Escreve tudo que o streamer fala e marca onde ele ficou alto
   (grito, surto) e, no YouTube, onde o chat acelerou.
3. **Separa os trechos mais quentes e a IA escolhe.** O script acha onde o streamer gritou, o chat acelerou e teve
   reação; a IA lê só esses trechos (rápido até na IA de graça) e dá nota pra cada momento.
4. **Monta os cortes.** Baixa só os minutos escolhidos, acha a câmera do streamer sozinha e coloca a legenda.

## Instalação

Você precisa do **Claude Code** (pode ser com a sua assinatura do Claude ou de graça, com o Ollama).

### Jeito de graça (Ollama) — precisa de 16 GB de memória ou mais

1. Baixe o Ollama em https://ollama.com/download e abra. Clique em **Continue** e depois em
   **"No thanks, I'll use Ollama locally"** (não precisa de conta).
2. Abra as **Settings** do Ollama (no Mac: menu Ollama → Settings…) e arraste o **Context length** de 4k para **64k**.
3. Feche o navegador e os outros programas (a IA usa quase toda a memória).
4. Abra o terminal (Mac: Command + Espaço → "Terminal"; Windows: Iniciar → "Windows PowerShell") e digite:
   ```
   mkdir cortes-gta
   cd cortes-gta
   ollama launch claude --model qwen3.5
   ```
   Com 32 GB ou mais, use `qwen3.5:27b`. Na primeira vez ele baixa a IA (~7,6 GB): o **Yes** já vem marcado, é só Enter.
5. Na pergunta "Is this a project you trust?", aperte a **seta pra baixo** até **"Yes, I trust this folder"** e Enter
   (a opção marcada de início é "No, exit"). Avisos amarelos como "isn't recognized" e "Not logged in" são normais.

### Com a assinatura do Claude

Baixe o app em https://claude.com/download (plano Pro ou maior), entre na aba **Code** e escolha uma pasta.
Sem terminal. Os cortes saem mais rápido e as escolhas ficam bem melhores.

### Colocando a skill (e atualizando)

Cole no Claude Code:

> instala essa skill e monta o clipper do GTA 6: https://github.com/Math7Braga/Teste-Clipper

Se a IA ficar em loop ou der erro, cole o comando direto (serve também pra **atualizar**):

- **Mac:** `curl -fsSL https://raw.githubusercontent.com/Math7Braga/Teste-Clipper/main/instalar.sh | bash`
- **Windows (PowerShell):** `irm https://raw.githubusercontent.com/Math7Braga/Teste-Clipper/main/instalar.ps1 | iex`

Ele baixa a skill, confere o que falta no seu computador, instala sozinho (inclusive o ffmpeg) e avisa quando tá pronto.

### Avisos

- Live trancada por idade ou só pra membros não baixa (é trava do YouTube). O `buscar` já pula essas.
- No jeito de graça, em computador mais simples, cada corte demora mais. É normal, deixa rodando.

## Usando

- "corta essa live: LINK"
- "acha as maiores lives de GTA 6 de hoje e corta"
- "faz 5 cortes dessa live: LINK"
- IA se enrolando? "faz os cortes no modo automático: LINK" (tudo sozinho, títulos mais simples)
- **Só um pedaço, até de live ao vivo (com DVR):** "corta essa live do 1:32:10 até 1:36:00: LINK" ou
  "corta os últimos 8 minutos dessa live: LINK" (veja a seção abaixo)

Live longa demora pra escutar (no modo de graça, o seu computador faz tudo). O trabalho roda sozinho em segundo
plano e guarda o progresso: se a IA mostrar "AINDA TRABALHANDO", é só deixar ela continuar.

Os cortes ficam na pasta `clipper-gta6/cortes` da sua pasta de usuário.

## Cortar um pedaço escolhido (inclusive live ao vivo com DVR)

Comandos (use `~/clipper-gta6/clip` no Mac/Linux ou `& "$HOME\clipper-gta6\clip.cmd"` no Windows):

```
clip trecho LINK --de 01:32:10 --ate 01:36:00     # horário do player do YouTube
clip trecho LINK --ultimos 8                      # últimos 8 minutos de uma live rolando agora
clip trecho LINK --de 01:32:10 --ate 01:36:00 --auto --quantos 2   # tudo sozinho
clip testar LINK                                  # amostra de 30 s: confere se o DVR dessa live baixa
```

Ele baixa só o pedaço, escuta só ele, a IA avalia só ele e monta os cortes (`escolher` e `fazer` funcionam igual).

- Precisa ser **YouTube** com o **DVR ligado** (dá pra voltar no tempo no player). Twitch e Kick só depois que a live acabar.
- Pegue 1 ou 2 minutos a mais antes e depois do momento: o horário pode errar alguns segundos e a IA acha o instante exato.
- O YouTube às vezes guarda só as últimas horas no DVR; momentos mais antigos que isso dão o aviso "já saiu do DVR".
- O trecho vira um arquivo de vídeo no seu computador (limite de 120 min, 1080p).

## Precisa ter

- Mac, Windows ou Linux
- Python 3.10 ou mais novo (se faltar, o instalador baixa um sozinho)
- ffmpeg: a skill baixa sozinha
- uns 2 GB livres pros modelos de escuta, mais o áudio das lives
- pra cortar a live inteira ela precisa ter acabado (ao vivo só pelo comando `trecho`, com DVR) e não pode ser trancada por idade/membros

## Respeite os streamers

Corte só quem libera cortes e mantenha o crédito que vem no `.txt` de cada corte.
