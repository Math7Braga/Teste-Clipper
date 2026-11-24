"""Thumbnail chamativa pros cortes do Clipper do GTA 6.

Uso:
    clip thumb NOME-DA-LIVE            # todas as thumbs da live (o fazer já chama sozinho no fim)
    clip thumb NOME-DA-LIVE --corte 3  # só a do corte 3

Para cada corte gera, na pasta cortes/NOME-DA-LIVE:
    thumb_NN.jpg  1280x720   (YouTube)
    capa_NN.jpg   1080x1920  (capa de Shorts / Reels / TikTok)

Como escolhe a imagem: procura os momentos em que o streamer ficou mais alto (grito, surto), tira vários
quadros em volta deles e fica com o mais nítido e colorido (pula tela de pausa e menu). Depois amplia o rosto
do streamer, satura as cores e escreve o título bem grande, com contorno grosso.
"""
import subprocess
import textwrap
from pathlib import Path

from comum import CORTES, YUNET, ler_json, pasta_da_live  # noqa: E402

FONTE = Path(__file__).resolve().parent.parent / "fontes" / "Montserrat-ExtraBold.ttf"

AMARELO, BRANCO, PRETO, VERMELHO = (255, 230, 0), (255, 255, 255), (0, 0, 0), (235, 30, 45)


# ------------------------------------------------------------------ escolher o quadro
def picos_de_volume(video, quantos=4):
    """Segundos em que o áudio ficou mais alto (o grito/surto do streamer)."""
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                       capture_output=True)
    a = np.frombuffer(r.stdout, dtype=np.int16).astype(np.float32)
    if a.size < 8000:
        return []
    jan = 4000  # meio segundo
    rms = np.sqrt(np.convolve(a ** 2, np.ones(jan) / jan, mode="valid")[::jan])
    ordem = np.argsort(-rms)
    picos = []
    for i in ordem:
        t = i * 0.5
        if all(abs(t - p) > 3 for p in picos):
            picos.append(t)
        if len(picos) >= quantos:
            break
    return picos


def nota_do_quadro(q):
    """Nítido e colorido = bom. Menu/pausa (borrado, cinza) = ruim."""
    import cv2
    import numpy as np
    p = cv2.resize(q, (480, 270))
    cinza = cv2.cvtColor(p, cv2.COLOR_BGR2GRAY)
    nitidez = cv2.Laplacian(cinza, cv2.CV_64F).var()
    b, g, r = [c.astype(np.float32) for c in cv2.split(p)]
    rg, yb = np.abs(r - g), np.abs(0.5 * (r + g) - b)
    cor = np.sqrt(rg.std() ** 2 + yb.std() ** 2) + 0.3 * np.sqrt(rg.mean() ** 2 + yb.mean() ** 2)
    brilho = cinza.mean()
    escuro = 0.4 if brilho < 45 else 1.0
    return (nitidez ** 0.5) * (cor ** 0.8) * escuro


def melhor_quadro(video):
    import cv2
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
    dur = n / fps
    tempos = []
    for p in picos_de_volume(video):
        tempos += [p - 0.6, p, p + 0.5, p + 1.2]
    tempos += [dur * k / 10 for k in range(1, 10)]  # e uns espalhados, por garantia
    melhor, nota_melhor = None, -1
    for t in tempos:
        t = min(max(t, 0), dur - 0.1)
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, q = cap.read()
        if not ok:
            continue
        nota = nota_do_quadro(q) * (1.15 if t in tempos[:16] else 1.0)
        if nota > nota_melhor:
            melhor, nota_melhor = q, nota
    cap.release()
    return melhor


def achar_rosto(q):
    """Caixa (x, y, l, a) do rosto do streamer, ou None."""
    import cv2
    if not YUNET.exists():
        return None
    H, W = q.shape[:2]
    esc = 960 / W
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (960, int(H * esc)), 0.7)
    _, rostos = det.detect(cv2.resize(q, (960, int(H * esc))))
    if rostos is None or not len(rostos):
        return None
    r = max(rostos, key=lambda r: r[14] * r[2])
    return [v / esc for v in r[:4]]


# ------------------------------------------------------------------ desenho
def imagem_viva(img, sat=1.45, contraste=1.18, brilho=1.06):
    from PIL import ImageEnhance
    img = ImageEnhance.Color(img).enhance(sat)
    img = ImageEnhance.Contrast(img).enhance(contraste)
    img = ImageEnhance.Brightness(img).enhance(brilho)
    return ImageEnhance.Sharpness(img).enhance(1.6)


def preencher(img, L, A, foco=(0.5, 0.5)):
    """Redimensiona cobrindo L×A, cortando em volta do ponto de foco."""
    w, h = img.size
    e = max(L / w, A / h)
    img = img.resize((int(w * e) + 1, int(h * e) + 1))
    w, h = img.size
    x = min(max(int(foco[0] * w - L / 2), 0), w - L)
    y = min(max(int(foco[1] * h - A / 2), 0), h - A)
    return img.crop((x, y, x + L, y + A))


def vinheta(img, forca=0.55):
    from PIL import Image, ImageDraw, ImageFilter
    L, A = img.size
    m = Image.new("L", (L, A), 0)
    ImageDraw.Draw(m).ellipse((-L * 0.25, -A * 0.25, L * 1.25, A * 1.25), fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(L, A) // 5))
    escuro = Image.new("RGB", (L, A), (0, 0, 0))
    return Image.composite(img, Image.blend(img, escuro, forca), m)


def raios(L, A, centro, cor=(255, 210, 0), n=18, alfa=70):
    """Raios saindo do rosto, estilo thumbnail de YouTube."""
    import math
    from PIL import Image, ImageDraw
    camada = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    R = (L ** 2 + A ** 2) ** 0.5
    cx, cy = centro
    for k in range(n):
        a1 = 2 * math.pi * k / n
        a2 = a1 + math.pi / n * 0.55
        d.polygon([(cx, cy), (cx + R * math.cos(a1), cy + R * math.sin(a1)),
                   (cx + R * math.cos(a2), cy + R * math.sin(a2))], fill=(*cor, alfa))
    return camada


def caixa_da_camera(img, rosto):
    """Acha as bordas da caixinha da câmera em volta do rosto (linhas retas fortes), pra não pegar o jogo junto."""
    import cv2
    import numpy as np
    W, H = img.size
    fx, fy, fw, fh = rosto
    g = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    bordas = cv2.Canny(g, 60, 160) > 0
    y0, y1 = int(max(0, fy - fh * 0.5)), int(min(H, fy + fh * 1.8))
    x0, x1 = int(max(0, fx - fw * 0.3)), int(min(W, fx + fw * 1.3))

    def linha(faixa, eixo, de, ate, passo):
        melhor, pos = 0.0, None
        for p in range(int(de), int(ate), passo):
            if not (0 <= p < (W if eixo == "x" else H)):
                break
            dens = (bordas[faixa, p].mean() if eixo == "x" else bordas[p, faixa].mean())
            if dens > melhor:
                melhor, pos = dens, p
        return pos if melhor > 0.4 else None

    esq = linha(slice(y0, y1), "x", fx - fw * 0.6, fx - fw * 4, -1)
    dir_ = linha(slice(y0, y1), "x", fx + fw * 1.6, fx + fw * 5, 1)
    # a borda de cima/baixo às vezes tem falhas no meio: mede na largura toda da caixinha
    xa = int(esq) if esq is not None else x0
    xb = int(dir_) if dir_ is not None else x1
    cima = linha(slice(xa, xb), "y", fy - fh * 0.25, fy - fh * 3, -1)
    baixo = linha(slice(xa, xb), "y", fy + fh * 1.15, fy + fh * 5, 1)
    m = 6  # entra um pouco pra dentro da borda
    return ((esq + m) if esq is not None else 0, (cima + m) if cima is not None else 0,
            (dir_ - m) if dir_ is not None else W, (baixo - m) if baixo is not None else H)


def recorte_rosto(img, rosto, proporcao, folga=2.6):
    """Recorta a câmera do streamer em volta do rosto, na proporção pedida (largura/altura), sem sair da caixinha."""
    bx0, by0, bx1, by1 = caixa_da_camera(img, rosto)
    fx, fy, fw, fh = rosto
    BW, BH = bx1 - bx0, by1 - by0
    ch = min(BH, fh * folga)
    cw = ch * proporcao
    if cw > BW:
        cw = BW
        ch = cw / proporcao
    cx = min(max(fx + fw / 2 - cw / 2, bx0), bx1 - cw)
    cy = min(max(fy + fh * 0.55 - ch / 2, by0), by1 - ch)
    return img.crop((int(cx), int(cy), int(cx + cw), int(cy + ch)))


def faixa_escura(L, A, y0, y1, alfa=170):
    """Faixa escura com degradê atrás do texto, pra ele saltar mesmo em fundo claro."""
    from PIL import Image, ImageDraw
    camada = Image.new("RGBA", (L, A), (0, 0, 0, 0))
    d = ImageDraw.Draw(camada)
    meio, alt = (y0 + y1) / 2, (y1 - y0) / 2
    for y in range(max(0, int(y0)), min(A, int(y1))):
        a = int(alfa * max(0.0, 1 - (abs(y - meio) / alt) ** 2.5))
        d.line([(0, y), (L, y)], fill=(0, 0, 0, a))
    return camada


def moldura(img, borda=12, cor=BRANCO, raio=28, sombra=True, angulo=0):
    from PIL import Image, ImageDraw, ImageFilter
    w, h = img.size
    W, H = w + 2 * borda, h + 2 * borda
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, W - 1, H - 1), raio + borda, fill=255)
    base.paste(Image.new("RGBA", (W, H), (*cor, 255)), (0, 0), m)
    mi = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mi).rounded_rectangle((0, 0, w - 1, h - 1), raio, fill=255)
    base.paste(img.convert("RGBA"), (borda, borda), mi)
    if angulo:
        base = base.rotate(angulo, resample=Image.BICUBIC, expand=True)
    if not sombra:
        return base
    s = 30
    out = Image.new("RGBA", (base.width + 2 * s, base.height + 2 * s), (0, 0, 0, 0))
    sh = Image.new("RGBA", base.size, (0, 0, 0, 200))
    out.paste(sh, (s + 10, s + 14), base.split()[3])
    out = out.filter(ImageFilter.GaussianBlur(14))
    out.alpha_composite(base, (s, s))
    return out


def quebrar(titulo, max_linhas=3):
    t = " ".join(str(titulo).upper().replace('"', "").replace("“", "").replace("”", "").split())
    for largura in range(10, 40):
        linhas = textwrap.wrap(t, largura)
        if len(linhas) <= max_linhas:
            return linhas
    return textwrap.wrap(t, 40)[:max_linhas]


def bloco_texto(linhas, largura_max, altura_max, destaque_ultima=True, contorno_rel=0.11):
    """Desenha as linhas do título num RGBA transparente, o maior possível dentro da caixa."""
    from PIL import Image, ImageDraw, ImageFont
    tam = 260
    while tam > 30:
        f = ImageFont.truetype(str(FONTE), tam)
        borda = max(4, int(tam * contorno_rel))
        alturas = [f.getbbox(l)[3] - f.getbbox(l)[1] for l in linhas]
        larguras = [f.getlength(l) for l in linhas]
        esp = int(tam * 0.12)
        total_h = sum(alturas) + esp * (len(linhas) - 1) + 2 * borda
        if max(larguras) + 2 * borda <= largura_max and total_h <= altura_max:
            break
        tam -= 6
    W, H = int(max(larguras) + 2 * borda + 20), int(total_h + 20)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    y = borda + 10
    for i, (l, h) in enumerate(zip(linhas, alturas)):
        x = (W - f.getlength(l)) / 2
        cor = AMARELO if (destaque_ultima and i == len(linhas) - 1 and len(linhas) > 1) or len(linhas) == 1 else BRANCO
        topo = f.getbbox(l)[1]
        d.text((x, y - topo), l, font=f, fill=cor, stroke_width=borda, stroke_fill=PRETO)
        y += h + esp
    return img


def com_sombra(camada, dx=8, dy=10, raio=10, alfa=180):
    from PIL import Image, ImageFilter
    s = raio * 2
    out = Image.new("RGBA", (camada.width + 2 * s + dx, camada.height + 2 * s + dy), (0, 0, 0, 0))
    preto = Image.new("RGBA", camada.size, (0, 0, 0, alfa))
    out.paste(preto, (s + dx, s + dy), camada.split()[3])
    out = out.filter(ImageFilter.GaussianBlur(raio))
    out.alpha_composite(camada, (s, s))
    return out


def selo(texto="GTA 6", tam=64, cor=VERMELHO, angulo=-6):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(str(FONTE), tam)
    w, h = int(f.getlength(texto)), f.getbbox(texto)[3]
    pad = int(tam * 0.35)
    img = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), int(tam * 0.25), fill=(*cor, 255),
                        outline=BRANCO, width=max(3, tam // 14))
    d.text((pad, pad - f.getbbox(texto)[1] + 2), texto, font=f, fill=BRANCO)
    return img.rotate(angulo, resample=Image.BICUBIC, expand=True)


def colar_centro(base, camada, cx, cy):
    base.alpha_composite(camada, (int(cx - camada.width / 2), int(cy - camada.height / 2)))


# ------------------------------------------------------------------ as duas thumbs
def thumb_youtube(quadro, rosto, titulo):
    """1280x720: jogo saturado no fundo, rosto grande à direita com raios, título enorme à esquerda."""
    from PIL import Image
    L, A = 1280, 720
    W, H = quadro.size
    foco = (0.5, 0.5)
    if rosto is not None:  # puxa o fundo pro lado oposto da câmera, pra mostrar mais jogo
        foco = (0.35 if rosto[0] > W / 2 else 0.65, 0.5)
    fundo = vinheta(imagem_viva(preencher(quadro, L, A, foco), sat=1.55), 0.5).convert("RGBA")
    if rosto is not None:
        cam = imagem_viva(recorte_rosto(quadro, rosto, 0.85), sat=1.3, contraste=1.12, brilho=1.1)
        cam = cam.resize((int(A * 0.86 * 0.85), int(A * 0.86)))
        cx, cy = L - cam.width / 2 - 40, A / 2 + 10
        fundo.alpha_composite(raios(L, A, (cx, cy)))
        area = L - cam.width - 110
    else:
        fundo.alpha_composite(raios(L, A, (L / 2, A / 2), alfa=45))
        area = L - 80
    fundo.alpha_composite(faixa_escura(L, A, A * 0.22, A * 0.95, alfa=150))
    if rosto is not None:
        colar_centro(fundo, moldura(cam, borda=12, angulo=-3), cx, cy)  # rosto por cima da faixa
    txt = com_sombra(bloco_texto(quebrar(titulo), area, A * 0.62).rotate(2, resample=Image.BICUBIC, expand=True))
    colar_centro(fundo, txt, 40 + area / 2, A * 0.58)
    colar_centro(fundo, selo(tam=58), 120, 75)
    return fundo.convert("RGB")


def capa_vertical(quadro, rosto, titulo):
    """1080x1920: rosto enorme em cima, título no meio, jogo embaixo."""
    from PIL import Image
    L, A = 1080, 1920
    W, H = quadro.size
    fundo = vinheta(imagem_viva(preencher(quadro, L, A), sat=1.5), 0.6).convert("RGBA")
    if rosto is not None:
        jogo = imagem_viva(preencher(quadro, L, 1000, (0.35 if rosto[0] > W / 2 else 0.65, 0.5)), sat=1.55)
        fundo.paste(jogo, (0, A - 1000))
        cam = imagem_viva(recorte_rosto(quadro, rosto, 1.0, folga=2.4), sat=1.3, contraste=1.12, brilho=1.1)
        cam = cam.resize((860, 860))
        fundo.alpha_composite(raios(L, A, (L / 2, 520), n=22))
        colar_centro(fundo, moldura(cam, borda=14, angulo=-2), L / 2, 500)
        y_txt = 1200
    else:
        fundo.alpha_composite(raios(L, A, (L / 2, A / 2), n=22, alfa=45))
        y_txt = A * 0.45
    fundo.alpha_composite(faixa_escura(L, A, y_txt - 360, y_txt + 360, alfa=175))
    txt = com_sombra(bloco_texto(quebrar(titulo), L - 70, 560).rotate(2, resample=Image.BICUBIC, expand=True))
    colar_centro(fundo, txt, L / 2, y_txt + 40)
    colar_centro(fundo, selo(tam=78), 170, 110)
    return fundo.convert("RGB")


# ------------------------------------------------------------------ principal
def gerar(pasta, so_corte=None):
    """Gera thumb_NN.jpg (YouTube) e capa_NN.jpg (Shorts/Reels/TikTok) pra cada corte já montado."""
    import cv2
    from PIL import Image
    escolhidos = ler_json(pasta / "escolhidos.json", {}).get("cortes", [])
    destino = CORTES / pasta.name
    destino.mkdir(parents=True, exist_ok=True)
    feitos = 0
    for i, m in enumerate(escolhidos, 1):
        if so_corte and i != so_corte:
            continue
        trecho = pasta / f"corte_{i:02d}" / "trecho.mp4"
        if not trecho.exists():
            print(f"  corte {i}: ainda não tem o trecho baixado (rode o 'fazer' antes), pulei")
            continue
        print(f"  thumbnail do corte {i}: {m.get('titulo', '')}", flush=True)
        q = melhor_quadro(trecho)
        if q is None:
            print("    não consegui ler o vídeo, pulei")
            continue
        rosto = achar_rosto(q)
        img = Image.fromarray(cv2.cvtColor(q, cv2.COLOR_BGR2RGB))
        titulo = m.get("titulo") or "OLHA O QUE ACONTECEU"
        thumb_youtube(img, rosto, titulo).save(destino / f"thumb_{i:02d}.jpg", quality=92)
        capa_vertical(img, rosto, titulo).save(destino / f"capa_{i:02d}.jpg", quality=92)
        feitos += 1
    print(f"THUMBS PRONTAS: {feitos} em {destino}  (thumb_NN.jpg = YouTube, capa_NN.jpg = Shorts/Reels/TikTok)")
    return feitos


def thumb(a):
    """Comando 'clip thumb NOME [--corte N]'."""
    gerar(pasta_da_live(a.live), a.corte)
