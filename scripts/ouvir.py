"""Passos 1 e 2: baixa só o áudio da live, escuta tudo no computador e separa o que a IA vai ler.

Sai, na pasta da live:
  candidatos.txt   os trechos mais "quentes" da live (gritos, chat acelerado, reações). A IA lê SÓ ESTE arquivo.
  blocos/          a live inteira em blocos de 12 minutos (só pra quem quiser ler tudo, mais lento)

Marcas nas falas:
  [ALTO +11dB]   o streamer ficou bem mais alto que o normal daquele trecho (grito, surto)
  [CHAT 3.4x]    no replay do YouTube, o chat andou 3,4 vezes mais rápido que o normal
"""
import json
import math
import os
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

from comum import (BLOCO_MIN, TRABALHO, gravar_json, hms, ler_json, motivo_trancada, rodar, segundos, slug, ytdlp)

PEDACO = 600  # escuta 10 minutos por vez e guarda: se parar no meio, continua dali
LINKS = TRABALHO / "links.json"


# ---------------------------------------------------------------- ler a live (rápido, em primeiro plano)
JANELA_MAX_MIN = int(os.environ.get("CLIPPER_JANELA_MAX_MIN", "120"))  # trecho maior que isso vira arquivo enorme
BORDA = 20  # os últimos segundos da live ainda estão sendo gravados


def resolver_janela(j, meta, ao_vivo):
    """Transforma o pedido da pessoa (--de/--ate ou --ultimos) em segundos da live."""
    inicio_ts = meta.get("release_timestamp") or meta.get("timestamp")
    agora = time.time() - float(inicio_ts) if (ao_vivo and inicio_ts) else None  # quanto tempo de live já passou
    try:
        if j.get("ultimos"):
            if agora is None:
                sys.exit("\n  ✗ Não consegui saber a hora em que essa live começou, então 'últimos minutos' não dá. "
                         "Use --de e --ate (o horário que aparece no player do YouTube).")
            e = agora - BORDA
            s = e - float(j["ultimos"]) * 60
        else:
            s, e = segundos(j["de"]), segundos(j["ate"])
    except (TypeError, ValueError):
        sys.exit("\n  ✗ Não entendi o horário. Use assim: --de 01:32:10 --ate 01:36:00 (hora:minuto:segundo).")
    if e < s:
        s, e = e, s
    s = max(0.0, s)
    if agora is not None and e > agora - BORDA:
        print(f"      (o fim pedido está colado no 'agora' da live: ajustei pra {hms(agora - BORDA)})", flush=True)
        e = agora - BORDA
    dur = float(meta.get("duration") or 0)
    if not ao_vivo and dur:
        e = min(e, dur)
    if e - s < 20:
        sys.exit("\n  ✗ O trecho ficou com menos de 20 segundos. Aumente o intervalo (--de / --ate).")
    if e - s > JANELA_MAX_MIN * 60:
        sys.exit(f"\n  ✗ O trecho tem mais de {JANELA_MAX_MIN} minutos. Escolha um intervalo menor "
                 "(vira um arquivo de vídeo grande no seu computador).")
    return s, e, agora


def ler_live(url, janela=None):
    """Lê título, duração e situação da live. Sai com aviso claro quando não dá pra baixar.
    Com `janela` ({"de","ate"} ou {"ultimos": minutos}) aceita live ainda ao vivo com DVR e guarda só esse trecho."""
    links = ler_json(LINKS, {})
    chave = url
    if janela:
        chave = f"{url}#" + (f"ultimos{janela['ultimos']}" if janela.get("ultimos") else f"{janela['de']}-{janela['ate']}")
    if chave in links and (TRABALHO / links[chave] / "info.json").exists():
        antigo = ler_json(TRABALHO / links[chave] / "info.json", {})
        # "últimos N minutos" muda a cada minuto: só reaproveita se o pedido tem menos de 20 min (rodar o mesmo comando de novo)
        if not (janela and janela.get("ultimos")) or time.time() - antigo.get("criado", 0) < 1200:
            return TRABALHO / links[chave]
    print(f"\n[1/4] Lendo a live: {url}", flush=True)
    r = subprocess.run(ytdlp() + ["-J", "--no-playlist", "--no-warnings", url], capture_output=True, text=True)
    if r.returncode != 0:
        motivo = motivo_trancada(r.stderr)
        if motivo:
            sys.exit(f"\n  ✗ NÃO DÁ PRA BAIXAR: {motivo}.\n    Isso é trava do site, não erro do clipper. "
                     "Escolha outra live (o 'buscar' já pula as trancadas).")
        if "kick.com" in url:
            sys.exit("\n  ✗ NÃO DÁ PRA BAIXAR: o Kick bloqueou o download dessa live agora.\n"
                     "    Quase todo streamer grande também passa a live no YouTube ou na Twitch: "
                     "use o link de lá (ou rode 'buscar').")
        print(r.stderr[-1200:])
        sys.exit("\n  ✗ Não consegui ler essa live. Confira se o link abre no navegador, rode 'instalar' "
                 "(atualiza o baixador) e tente de novo.")
    meta = json.loads(r.stdout)
    situacao = meta.get("live_status")
    ao_vivo = situacao in ("is_live", "post_live")
    youtube = (meta.get("extractor_key") or "").lower().startswith("youtube")
    if janela:
        if situacao == "is_upcoming":
            sys.exit("\n  ✗ ESSA LIVE AINDA NEM COMEÇOU.\n    Espere ela começar (e o DVR ter alguns minutos).")
        if ao_vivo and not youtube:
            sys.exit("\n  ✗ ESSA LIVE AINDA ESTÁ AO VIVO e só o YouTube deixa voltar no tempo (DVR) por aqui.\n"
                     "    Na Twitch/Kick espere a live acabar, ou use o link da mesma live no YouTube.")
    else:
        if situacao in ("is_live", "is_upcoming"):
            sys.exit("\n  ✗ ESSA LIVE AINDA ESTÁ AO VIVO (ou nem começou).\n    Pra cortar durante a live, use o comando "
                     "'trecho' (escolhe o pedaço e precisa do DVR ligado). Pra live inteira, espere ela acabar "
                     "(o 'buscar' mostra as de hoje que já acabaram).")
        if situacao == "post_live":
            sys.exit("\n  ✗ ESSA LIVE ACABOU AGORA e o site ainda está processando o vídeo.\n"
                     "    Tente de novo daqui a algumas horas, ou escolha outra live.")
    s = e = None
    if janela:
        s, e, _ = resolver_janela(janela, meta, ao_vivo)
    nome = slug(f"{meta.get('uploader') or meta.get('channel') or 'live'}-{meta.get('title', '')}", 50)
    if janela:
        nome += f"-trecho-{hms(s).replace(':', '')}-{hms(e).replace(':', '')}"
    pasta = TRABALHO / nome
    pasta.mkdir(parents=True, exist_ok=True)
    info = {k: meta.get(k) for k in ("id", "title", "uploader", "channel", "duration", "view_count",
                                     "webpage_url", "extractor_key", "was_live", "live_status")}
    info["url"] = url
    info["criado"] = time.time()
    if janela:
        info["ao_vivo"] = ao_vivo
        info["inicio_ts"] = meta.get("release_timestamp") or meta.get("timestamp")
        info["janela"] = {"inicio": s, "fim": e, "pedido": [s, e]}  # vira o horário real depois de baixar
    gravar_json(pasta / "info.json", info)
    links[chave] = nome
    gravar_json(LINKS, links)
    dur = info.get("duration") or 0
    print(f"      {info['title']}  |  {info.get('uploader')}  |  "
          + (f"trecho {hms(s)}–{hms(e)}" + (" (live ainda ao vivo)" if ao_vivo else "") if janela else hms(dur)), flush=True)
    return pasta


# ---------------------------------------------------------------- download do áudio (+ chat)
def audio_pronto(pasta):
    ok = [p for p in pasta.glob("audio.*") if p.suffix not in (".part", ".ytdl", ".temp")
          and not list(pasta.glob(p.name + ".part"))]
    return None if list(pasta.glob("audio.*.part")) else (ok[0] if ok else None)


def baixar_audio(pasta):
    info = ler_json(pasta / "info.json", {})
    url = info["url"]
    if not audio_pronto(pasta):
        print("\n[1/4] Baixando só o áudio da live (continua de onde parou se cair)…", flush=True)
        rodar(ytdlp() + ["-f", "ba/b", "-x", "--no-playlist", "--no-warnings", "-q", "--progress", "--newline",
                         "--progress-delta", "15", "--progress-template",
                         "download:      baixado %(progress._percent_str)s", "--continue",
                         "-o", str(pasta / "audio.%(ext)s"), url])
    if (info.get("extractor_key") or "").lower().startswith("youtube") and not (pasta / "chat.feito").exists():
        print("      pegando o replay do chat (se a live tiver)…", flush=True)
        try:
            rodar(ytdlp() + ["--skip-download", "--write-subs", "--sub-langs", "live_chat", "--no-warnings", "-q",
                             "-o", str(pasta / "chat"), url], timeout=900)
        except Exception as e:  # sem chat não é erro: só não tem a marca [CHAT]
            print(f"      sem replay de chat ({type(e).__name__})", flush=True)
        (pasta / "chat.feito").write_text("ok")


def wav16k(pasta):
    w = pasta / "audio16k.wav"
    if not w.exists():
        audio = pasta / "janela.mp4" if (pasta / "janela.mp4").exists() else audio_pronto(pasta)
        tmp = pasta / "audio16k.tmp.wav"
        print("      preparando o áudio pra escutar…", flush=True)
        rodar(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-ac", "1", "-ar", "16000", tmp])
        tmp.replace(w)
    return w


# ---------------------------------------------------------------- transcrição (10 min por vez, com progresso salvo)
def deslocamento(pasta):
    """Segundo da live em que o trecho baixado começa (0 quando é a live inteira)."""
    return float((ler_json(pasta / "info.json", {}).get("janela") or {}).get("inicio", 0))


def modelo_padrao():
    return "base" if (os.cpu_count() or 4) >= 6 else "tiny"


def transcrever(pasta, modelo=None, idioma=None):
    saida = pasta / "transcricao.json"
    if saida.exists():
        return ler_json(saida)
    import numpy as np
    from faster_whisper import WhisperModel
    modelo = modelo or modelo_padrao()
    w = wav16k(pasta)
    with wave.open(str(w)) as f:
        sr, n = f.getframerate(), f.getnframes()
    total = n / sr
    partes = max(1, math.ceil(total / PEDACO))
    pdir = pasta / "escuta"
    pdir.mkdir(exist_ok=True)
    print(f"\n[2/4] Escutando a live aqui no computador ({hms(total)}, {partes} partes de 10 min)…", flush=True)
    m, t0, feitas, lingua = None, time.time(), 0, idioma
    for k in range(partes):
        arq = pdir / f"{k:04d}.json"
        if arq.exists():
            continue
        if m is None:
            m = WhisperModel(modelo, device="cpu", compute_type="int8")
        with wave.open(str(w)) as f:
            f.setpos(min(n, k * PEDACO * sr))
            a = np.frombuffer(f.readframes(PEDACO * sr), dtype=np.int16).astype(np.float32) / 32768
        segs, inf = m.transcribe(a, language=lingua, vad_filter=True, beam_size=1, condition_on_previous_text=False)
        out = [[round(s.start + k * PEDACO, 2), round(s.end + k * PEDACO, 2), s.text.strip()]
               for s in segs if s.text.strip()]
        if lingua is None and (inf.language_probability or 0) > 0.8 and out:
            lingua = inf.language  # fixa a língua quando tem certeza (fica mais rápido e mais certo)
        gravar_json(arq, {"idioma": inf.language, "segmentos": out})
        feitas += 1
        falta = (time.time() - t0) / feitas * (partes - k - 1)
        print(f"      escutei {hms(min(total, (k + 1) * PEDACO))} de {hms(total)} "
              f"({100 * (k + 1) / partes:.0f}%), falta uns {int(falta / 60) + 1} min", flush=True)
    segs, linguas = [], {}
    off = deslocamento(pasta)  # no modo trecho, os tempos passam a ser os da live (o mesmo que aparece no player)
    for k in range(partes):
        d = ler_json(pdir / f"{k:04d}.json", {})
        segs += [[round(a + off, 2), round(b + off, 2), x] for a, b, x in d.get("segmentos", [])]
        if d.get("segmentos"):
            linguas[d.get("idioma")] = linguas.get(d.get("idioma"), 0) + len(d["segmentos"])
    dados = {"idioma": idioma or (max(linguas, key=linguas.get) if linguas else None), "segmentos": segs}
    gravar_json(saida, dados)
    return dados


# ---------------------------------------------------------------- picos de volume
def picos_de_volume(pasta):
    import numpy as np
    saida = pasta / "volume.json"
    if saida.exists():
        return ler_json(saida)
    dbs = []
    with wave.open(str(wav16k(pasta))) as f:  # lê aos poucos: live de 10 h não cabe inteira na memória
        sr = f.getframerate()
        while True:
            q = f.readframes(sr * 600)
            if not q:
                break
            a = np.frombuffer(q, dtype=np.int16).astype(np.float32)
            seg = len(a) // sr
            if seg == 0:
                break
            rms = np.sqrt(np.mean(a[: seg * sr].reshape(seg, sr) ** 2, axis=1) + 1e-6)
            dbs.append(20 * np.log10(rms / 32768 + 1e-9))
    db = np.concatenate(dbs) if dbs else np.zeros(1)
    seg = len(db)
    fala = db > np.percentile(db, 20)                       # ignora silêncio no cálculo da base
    base = np.zeros_like(db)
    for i in range(0, seg, 60):                             # "normal" = mediana dos 5 min em volta
        j0, j1 = max(0, i - 150), min(seg, i + 150)
        janela = db[j0:j1][fala[j0:j1]]
        base[i:i + 60] = np.median(janela) if len(janela) else np.median(db)
    excesso = db - base
    corte = max(8.0, float(np.percentile(excesso, 98)))
    off = int(deslocamento(pasta))
    picos = [[int(i) + off, round(float(excesso[i]), 1)] for i in np.where(excesso >= corte)[0]]
    gravar_json(saida, picos)
    return picos


# ---------------------------------------------------------------- velocidade do chat
def picos_do_chat(pasta):
    import numpy as np
    arq = next(iter(pasta.glob("chat*.live_chat.json")), None)
    if not arq:
        return []
    tempos = []
    with open(arq, encoding="utf-8", errors="ignore") as f:
        for linha in f:
            try:
                ms = json.loads(linha)["replayChatItemAction"]["videoOffsetTimeMsec"]
                tempos.append(int(ms) / 1000)
            except (KeyError, ValueError, json.JSONDecodeError):
                continue
    if len(tempos) < 50:
        return []
    caixas = np.bincount((np.array(tempos) // 10).astype(int))   # mensagens a cada 10 s
    picos = []
    for i, c in enumerate(caixas):
        viz = caixas[max(0, i - 30): i + 30]
        normal = max(1.0, float(np.median(viz)))
        if c >= 8 and c / normal >= 2.5:
            picos.append([i * 10, round(c / normal, 1)])
    return picos


# ---------------------------------------------------------------- texto que a IA lê
def _linha(s, e, t, vol, chat):
    marca = ""
    alto = max((vol.get(x, 0) for x in range(int(s), int(e) + 1)), default=0)
    if alto:
        marca += f"  [ALTO +{alto:.0f}dB]"
    ch = max((r for c, r in chat if s - 10 <= c <= e), default=0)
    if ch:
        marca += f"  [CHAT {ch}x]"
    return f"[{hms(s)}] {t}{marca}"


def blocos(pasta, trans, volume, chat):
    pb = pasta / "blocos"
    pb.mkdir(exist_ok=True)
    (pasta / "momentos").mkdir(exist_ok=True)
    vol = dict((s, e) for s, e in volume)
    segs = trans["segmentos"]
    fim = segs[-1][1] if segs else 0
    passo = BLOCO_MIN * 60
    n = 0
    primeiro = int(segs[0][0] // passo * passo) if segs else 0
    for k, ini in enumerate(range(primeiro, int(fim) + 1, passo), start=primeiro // passo + 1):
        linhas = [_linha(s, e, t, vol, chat) for s, e, t in segs if ini <= s < ini + passo]
        if not linhas:
            continue
        n += 1
        cab = (f"# BLOCO {k:02d} — de {hms(ini)} a {hms(ini + passo)}\n"
               f"# Escreva os momentos deste bloco em: momentos/bloco_{k:02d}.json\n\n")
        (pb / f"bloco_{k:02d}.txt").write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    return n


REACAO = re.compile(r"(meu deus|caralho|porra|n[ãa]o acredito|que isso|mds|kkk+|ha(ha)+|rs(rs)+|nossa|cara+lho|"
                    r"oh my god|what the|no way|holy|wtf|insane|crazy|let'?s go|bro what|ai meu|socorro|pqp)", re.I)


def candidatos(pasta, trans, volume, chat, quantos=12, janela=150, intervalo=None):
    """Os trechos mais quentes da live, sem se sobrepor. É o que a IA lê: rápido até numa IA pequena.
    Com `intervalo` (modo trecho) a IA lê o trecho escolhido de ponta a ponta, em pedaços seguidos de 2,5 min."""
    import numpy as np
    segs = trans["segmentos"]
    if not segs:
        return 0
    fim = int(segs[-1][1]) + 1
    ini0 = int(intervalo[0]) if intervalo else 0
    calor = np.zeros(fim + janela)
    for s, e in volume:
        if int(s) < len(calor):
            calor[int(s)] += e
    for c, r in chat:
        calor[int(c):int(c) + 10] += r * 3
    for s, e, t in segs:
        if int(s) < len(calor):
            calor[int(s)] += 5 * len(REACAO.findall(t)) + 0.03 * len(t.split())
    if not intervalo:
        calor[:240] *= 0.3            # começo da live: chat sempre explode no "boa noite", não é momento
        calor[max(0, fim - 240):] *= 0.3  # fim: despedida
    soma_toda = np.convolve(calor, np.ones(janela), "valid")
    soma = soma_toda[:max(1, fim - janela // 2)]
    escolhidos = []
    if intervalo:  # trecho escolhido pela pessoa: lê tudo em ordem (se for enorme, só os pedaços mais quentes)
        todos = list(range(ini0, fim, janela))
        escolhidos = sorted(sorted(todos, key=lambda i: -float(soma_toda[i]))[:max(quantos, 1)])
    else:
        for i in np.argsort(-soma):
            if len(escolhidos) >= quantos:
                break
            if all(abs(int(i) - j) >= janela for j in escolhidos):
                escolhidos.append(int(i))
        escolhidos.sort()
    if not escolhidos:
        return 0
    soma = soma_toda if intervalo else soma
    topo = max(float(soma[i]) for i in escolhidos) or 1
    vol = dict((s, e) for s, e in volume)
    partes, meta = [], []
    for n, i in enumerate(escolhidos, 1):
        linhas = [_linha(s, e, t, vol, chat) for s, e, t in segs if i <= s < i + janela]
        if not linhas:
            continue
        pico = i + int(np.argmax(np.convolve(calor[i:i + janela], np.ones(10), "same")))
        nota = round(100 * float(soma[i]) / topo)
        meta.append({"trecho": n, "inicio": i, "fim": i + janela, "pico": pico, "calor": nota})
        partes.append(f"## TRECHO {n:02d} — de {hms(i)} a {hms(i + janela)} (calor {nota})\n" + "\n".join(linhas))
    (pasta / "momentos").mkdir(exist_ok=True)
    cab = (("# O TRECHO ESCOLHIDO DA LIVE (os horários são os da live, iguais aos do player)\n" if intervalo else
            "# OS TRECHOS MAIS QUENTES DA LIVE\n") +
           "# Leia todos e escreva os melhores momentos em: momentos/candidatos.json (formato no SKILL.md).\n"
           "# 'calor' = o quanto o streamer gritou, o chat acelerou e teve reação. Mesmo assim, confirme pela fala.\n\n")
    (pasta / "candidatos.txt").write_text(cab + "\n\n".join(partes) + "\n", encoding="utf-8")
    gravar_json(pasta / "candidatos.json", meta)
    return len(partes)


# ---------------------------------------------------------------- baixar o trecho escolhido (modo trecho)
def baixar_trecho_escolhido(pasta):
    """Baixa só o pedaço pedido (ao vivo com DVR ou live acabada) em janela.mp4 e guarda a hora real em que começa."""
    from cortar import baixar_janela
    info = ler_json(pasta / "info.json", {})
    jan = info["janela"]
    s, e = jan["pedido"]
    if not (pasta / "janela.mp4").exists():
        print(f"\n[1/4] Baixando só o trecho {hms(s)}–{hms(e)} da live (continua mesmo se este comando for cortado)…",
              flush=True)
    inicio, jeito = baixar_janela(pasta, info, s, e)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(pasta / "janela.mp4")], capture_output=True, text=True)
    dur = float(r.stdout.strip() or (e - s))
    info["janela"] = {"inicio": inicio, "fim": inicio + dur, "pedido": [s, e], "estrategia": jeito}
    gravar_json(pasta / "info.json", info)
    print(f"      trecho baixado: {hms(inicio)}–{hms(inicio + dur)} ({jeito})", flush=True)


# ---------------------------------------------------------------- o trabalho inteiro (em segundo plano)
def trabalho_preparar(pasta, modelo=None, idioma=None, trechos=12):
    info = ler_json(pasta / "info.json", {})
    if info.get("janela"):
        baixar_trecho_escolhido(pasta)
    else:
        baixar_audio(pasta)
    trans = transcrever(pasta, modelo, idioma)
    print("\n[2/4] Marcando onde o streamer ficou alto e onde o chat acelerou…", flush=True)
    volume = picos_de_volume(pasta)
    chat = [] if info.get("janela") else picos_do_chat(pasta)
    blocos(pasta, trans, volume, chat)
    jan = info.get("janela") and ler_json(pasta / "info.json", {}).get("janela")
    n = candidatos(pasta, trans, volume, chat, quantos=trechos, intervalo=(jan["inicio"], jan["fim"]) if jan else None)
    print(f"      {len(volume)} segundos de grito/surto, {len(chat)} picos de chat, {n} trechos pra IA ler", flush=True)
