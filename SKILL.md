---
name: clipper-gta6
description: Clipper do GTA 6 — transforma lives longas de streamers (YouTube, Twitch ou Kick) em cortes verticais prontos pra postar, com a câmera do streamer em cima, o jogo embaixo, título de gancho, legenda palavra por palavra e a legenda do post com hashtags. Use quando a pessoa disser "monta o clipper do GTA 6", "instala essa skill", "corta essa live", "faz cortes dessa live", "acha as maiores lives de GTA 6 de hoje e corta", ou colar um link de live pedindo cortes, ou pedir um pedaço específico / os últimos minutos de uma live ao vivo.
---

# Clipper do GTA 6

Você (a IA) faz só uma parte do trabalho: **ler os trechos quentes da live e escolher os momentos**. Todo o resto
(baixar, escutar, achar a câmera, montar o vídeo e a legenda) é feito pelos scripts, no computador da pessoa.

Fale com a pessoa em português simples, uma frase por vez, sem jargão. Ela não é programadora.

## Regras que evitam travar

1. **Sempre o atalho.** Depois de instalado, todo comando é:
   - Mac / Linux / Git Bash: `~/clipper-gta6/clip COMANDO`
   - Windows PowerShell: `& "$HOME\clipper-gta6\clip.cmd" COMANDO`
   Se o atalho não existir, instale (passo 0). Não procure Python, não crie ambiente, não instale pacote na mão.
2. **"AINDA TRABALHANDO" não é erro.** O trabalho pesado roda sozinho em segundo plano. Diga à pessoa em que
   ponto está (a porcentagem que apareceu) e rode **o mesmo comando de novo**. Nada recomeça do zero.
   Se o comando for cortado por tempo, também é só rodar de novo.
3. **Mensagem com "NÃO DÁ PRA BAIXAR", "AINDA ESTÁ AO VIVO" ou "NÃO CONSEGUI BAIXAR ESSE TRECHO"**: repita pra pessoa com essas palavras (é trava do
   site, não do clipper) e ofereça outra live (`buscar`). Nunca diga "o YouTube não deixa baixar".
4. Não tente baixar vídeo, ler site ou escrever script por conta própria. Tudo que precisa está nos comandos abaixo.
5. Se você não conseguir escrever o arquivo de momentos depois de 2 tentativas, use o modo automático:
   `escolher NOME --auto --manter N` e depois `fazer NOME`.

## 0. "Instala essa skill" / "atualiza a skill" / "monta o clipper do GTA 6"

Rode **um comando só** (baixa a skill, arruma o Python sozinho se faltar e instala tudo; pode levar uns minutos):

- Mac/Linux: `curl -fsSL https://raw.githubusercontent.com/Math7Braga/Teste-Clipper/main/instalar.sh | bash`
- Windows (PowerShell): `irm https://raw.githubusercontent.com/Math7Braga/Teste-Clipper/main/instalar.ps1 | iex`

Quando aparecer **TUDO PRONTO**, diga: "Pronto, o clipper tá instalado. É só me mandar o link de uma live (YouTube,
Twitch ou Kick) ou pedir as maiores lives de GTA 6 de hoje."
Se der erro, rode o mesmo comando de novo uma vez. Se repetir, mostre à pessoa a última linha do erro.

## 1. "Acha as maiores lives de GTA 6 de hoje"

`buscar` (padrão: 7 lives, só as que já acabaram e dá pra baixar). Mostre a lista (título, canal, duração, views)
e pergunte quais cortar, ou corte a primeira se a pessoa já pediu pra cortar direto.

## 2. "Corta essa live" / "faz 5 cortes dessa live"

Número de cortes: o que a pessoa pediu (sem número = 3).

### 2.1 Preparar
`preparar LINK`. Baixa só o áudio, escuta a live inteira e separa os **trechos mais quentes** (gritos, chat
acelerado, reações) em `candidatos.txt`. Live longa demora: siga a regra 2 até aparecer **PRONTO PRA ESCOLHER**.
Se a live não for em português nem em inglês, passe `--idioma` (ex.: `--idioma es`).

### 2.2 Escolher os momentos (esta é a sua parte)
Leia **só** `~/clipper-gta6/trabalho/NOME/candidatos.txt` (o caminho aparece no fim do `preparar`) e escreva
`~/clipper-gta6/trabalho/NOME/momentos/candidatos.json`. Escreva uns 2 momentos a mais do que a pessoa pediu.

Cada linha é `[hh:mm:ss] fala`. As marcas ajudam:
- `[ALTO +12dB]`: o streamer ficou muito mais alto que o normal ali (grito, surto, susto).
- `[CHAT 3.1x]`: o chat andou 3 vezes mais rápido que o normal, alguma coisa aconteceu.
Marca sozinha não é momento. Confirme pela fala.

**O que vale um corte** (o que as pessoas compartilham):
- primeira reação a algo do jogo (ver o mapa, um personagem, um gráfico pela primeira vez)
- descoberta absurda ou detalhe que ninguém tinha visto
- surto, grito, raiva, susto
- falha engraçada, bug, morte ridícula
- opinião forte ou polêmica ("isso aqui tá pior que o GTA 5")
- história ou piada que fecha sozinha

**Seja rigoroso. Jogue fora:**
- o que precisa de contexto de antes pra fazer sentido
- o que começa com enrolação ("é…", "então…", "tipo assim", "voltando…", "uh, so yeah")
- leitura de doação, propaganda, conversa sobre a própria live, pausa, tela de carregamento
- fala picada ou que a transcrição não deixa entender

**Nota de 0 a 100.** 90+ = qualquer pessoa para de rolar o feed. 70–89 = bom. Abaixo de 60, nem escreva.
Nem todo trecho tem momento bom: não invente pra encher.

**Duração:** de 20 a 60 segundos. Comece 1–2 segundos antes da frase ou do grito que prende (nunca no meio de uma
palavra) e termine logo depois da reação/conclusão.

Formato de `momentos/candidatos.json`:

```json
[
  {
    "inicio": "01:12:03",
    "fim": "01:12:41",
    "nota": 88,
    "tipo": "primeira reação",
    "titulo": "ESSE MAPA NÃO TEM FIM E ELE SURTOU",
    "porque": "grita ao ver o mapa inteiro; fecha sozinho sem precisar de contexto",
    "post": "Ele abriu o mapa do GTA 6 e perdeu a voz. Você esperava esse tamanho? 😳 #gta6 #gtavi #gta #cortes #streamer"
  }
]
```

- `titulo`: o gancho que vai escrito no vídeo e na thumbnail. Curto (até ~45 letras), em MAIÚSCULAS, na língua da
  live, sem spoiler do final. Use o nome ou apelido do streamer quando ajudar ("CASIMIRO NÃO ACREDITOU…").
- `post`: legenda do post, 1–2 frases + 4 a 6 hashtags (sempre `#gta6`).

**Título e legenda têm que ser CHAMATIVOS e EMPOLGANTES** (pedido do dono do canal). A pessoa decide em 1 segundo
se para de rolar o feed, então cada frase tem que ter efeito:
- **Abra a curiosidade e não feche:** "NINGUÉM ESPERAVA O QUE TINHA DENTRO DO BARCO", "ELE NÃO DEVIA TER APERTADO ESSE
  BOTÃO", "O QUE ACONTECEU AQUI É ABSURDO".
- **Exagere a emoção que existiu de verdade:** "SURTOU", "PERDEU A CABEÇA", "FICOU SEM PALAVRAS", "QUASE CHOROU",
  "O CHAT EXPLODIU". Verbo forte, nada de "ficou surpreso" ou "achou legal".
- **Use número e contraste quando tiver:** "15 HORAS DE LIVE E AINDA RECLAMARAM", "NO GTA 5 ISSO ERA IMPOSSÍVEL".
- **Fale com quem assiste:** "VOCÊ NÃO VAI ACREDITAR…", "REPARA NO FUNDO…", "ESPERA ATÉ O FINAL".
- **Sem frase morna, sem explicação:** corte artigo e palavra de enchimento. "O MAPA DO GTA 6 É GIGANTE" →
  "ESSE MAPA NÃO TEM FIM 😳".
- **Legenda do post:** comece com uma frase de impacto (gancho ou pergunta que provoca comentário: "Você teria
  coragem?", "Isso é bug ou é genial?"), depois 1 emoji forte e as hashtags. Pode usar 1–2 emojis, não encha.
- **Varie:** não repita a mesma fórmula em todos os cortes da mesma live.
- **Limite: chamativo, não mentiroso.** O que o título promete tem que aparecer no corte. Se o título enganar, quem
  assiste sai antes do fim, a plataforma derruba o alcance e o streamer fica mal visto. Nada de inventar morte,
  briga, polêmica ou spoiler que não existe.

Se a pessoa quiser os melhores da live INTEIRA (mais lento), leia também os `blocos/bloco_NN.txt` e escreva
`momentos/bloco_NN.json` no mesmo formato.

### 2.3 Ficar com os melhores
`escolher NOME --manter N` (N = quantos cortes a pessoa pediu). Ele aceita o JSON mesmo com pequenos erros, junta
tudo, ordena pela nota e tira os que se sobrepõem. Conte: "Achei N momentos e fiquei com os melhores: …".

### 2.4 Montar os cortes
`fazer NOME`. Baixa só os segundos escolhidos, acha a câmera do streamer e monta o vídeo 1080×1920: câmera em cima,
jogo embaixo, título de gancho, legenda palavra por palavra. Sem câmera, usa o jogo inteiro com fundo desfocado.
Siga a regra 2 até aparecer **CORTES PRONTOS**.

Saída: `~/clipper-gta6/cortes/NOME/corte_01.mp4` + `corte_01.txt` (legenda do post + crédito da live).
Diga onde estão e que é só postar. No Mac, abra a pasta pra pessoa: `open ~/clipper-gta6/cortes/NOME`
(Windows: `explorer "$HOME\clipper-gta6\cortes\NOME"`).

### 2.5 Thumbnails
O `fazer` já faz sozinho, no fim, a thumbnail de cada corte: `thumb_01.jpg` (1280×720, YouTube) e `capa_01.jpg`
(1080×1920, capa de Shorts/Reels/TikTok), na mesma pasta dos vídeos. Pega o quadro do grito mais alto, amplia o rosto do
streamer e escreve o título do corte bem grande. Pra refazer: `thumb NOME` (ou `thumb NOME --corte 3` pra uma só).
Se você mudou o título de um corte no JSON, rode `escolher` e `fazer` de novo (ele refaz as thumbs também).

## 2B. "Corta só esse pedaço da live" / live que está rolando AGORA (precisa do DVR ligado)

Use quando a pessoa disser o horário do momento ("de 1h32 até 1h36", "os últimos 8 minutos") ou quando a live ainda
está ao vivo. Funciona também com live já acabada. O clipper baixa **só esse pedaço**, escuta só ele e a IA avalia só ele.

- Horário do player do YouTube: `trecho LINK --de 01:32:10 --ate 01:36:00`
- Últimos minutos de uma live que está rolando: `trecho LINK --ultimos 8`
- Tudo sozinho (sem a IA escolher): acrescente `--auto --quantos 3`
- Dica pra pessoa: **pegue uns 1 a 2 minutos a mais** antes e depois do momento. O horário pode errar alguns segundos
  e a IA acha o instante exato dentro do trecho.
- Máximo de 120 minutos por trecho (vira um arquivo de vídeo grande no computador).

Depois é igual ao passo 2: siga a regra 2 até **PRONTO PRA ESCOLHER**, leia o `candidatos.txt` (aqui ele traz o trecho
inteiro, em ordem, com os horários da live), escreva `momentos/candidatos.json`, rode `escolher NOME --manter N` e
`fazer NOME`. Os horários que você escreve no JSON são os da live (os mesmos do `candidatos.txt`).

Se a live ao vivo não deixar baixar: rode `testar LINK` (baixa 30 s de amostra e diz se o DVR funciona e por qual
jeito). Mensagens comuns: "DVR desligado" (o streamer não deixa voltar no tempo: só dá depois que a live acabar) e
"já saiu do DVR" (o YouTube só guarda as últimas horas: escolha um momento mais recente). Só o YouTube tem DVR por
aqui: Twitch e Kick, só depois que a live acabar.

## Tudo automático (IA com dificuldade ou pessoa com pressa)
`automatico LINK --quantos N` faz preparar + escolher + fazer sozinho, pelos trechos mais quentes. Os títulos ficam
mais simples (a frase mais forte do trecho). Siga a regra 2.

## Várias lives
Rode `preparar` com um link por vez (cada um até ficar PRONTO PRA ESCOLHER), depois escolher e fazer pra cada uma.

## Problemas comuns
- `status` mostra em que passo cada live está e o que está rodando agora.
- Momento ruim: apague-o do `momentos/candidatos.json`, rode `escolher` de novo e `fazer` (só refaz o que mudou).
- Erro de download que não seja trava do site: `instalar` (atualiza o baixador) e o mesmo comando de novo.
- Demorando muito: no modo de graça o computador da pessoa faz tudo. Explique isso, é normal em PC mais simples.

## Respeito aos streamers
Corte só de streamers que permitem cortes (muitos têm canal oficial de cortes e liberam). O `.txt` de cada corte já
traz o crédito com o link da live: mantenha na postagem.
