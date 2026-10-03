#!/usr/bin/env python3
"""
Rádio Local - Servidor de streaming de áudio para rede local
=============================================================
Execute este script no computador que terá a rádio.
Coloque arquivos MP3 na pasta 'musica'.

Novidade: pressione e segure a tecla R para falar no microfone
e interromper a música para todos os ouvintes (modo DJ).
"""

import os
import sys
import socket
import time
import threading
import queue
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
PORTA = 7074  # Altere aqui ou use: python radio_server.py 8080
PASTA_MUSICA = Path(__file__).parent / "musica"
TIPOS_SUPORTADOS = {".mp3", ".ogg", ".wav", ".m4a", ".flac"}
ICY_META_INTERVAL = 16000  # bytes entre metadados ICY

# Fila de anúncios que devem ser inseridos no stream de todos os clientes.
# Cada item é o conteúdo binário completo de um MP3 (bytes).
fila_anuncios = queue.Queue()

# Flag global: True enquanto o DJ está falando (gravação em andamento)
gravando = False
lock_gravacao = threading.Lock()

# ---------------------------------------------------------------------------
# Dependências opcionais para o microfone
# ---------------------------------------------------------------------------
TEM_MICROFONE = False
FFMPEG_OK = False

def _configurar_ffmpeg():
    """
    Tenta localizar o ffmpeg e configura o pydub.
    Retorna o caminho do executável ou None.
    """
    import shutil
    from pathlib import Path as _Path

    # 1) Já está no PATH?
    caminho = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    if caminho:
        return caminho

    # 2) Mesma pasta do script (solução mais simples)
    pasta_script = _Path(__file__).parent
    candidatos = [
        str(pasta_script / "ffmpeg.exe"),
        str(pasta_script / "ffmpeg" / "ffmpeg.exe"),
        str(pasta_script / "bin" / "ffmpeg.exe"),
        # Locais comuns no Windows
        r"L:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
        str(_Path.home() / "ffmpeg" / "bin" / "ffmpeg.exe"),
        str(_Path.home() / "scoop" / "apps" / "ffmpeg" / "current" / "bin" / "ffmpeg.exe"),
    ]

    # Procura em pastas do WinGet (nome da pasta varia)
    winget_base = _Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_base.exists():
        for pasta in winget_base.glob("*ffmpeg*"):
            for exe in pasta.rglob("ffmpeg.exe"):
                candidatos.append(str(exe))

    for c in candidatos:
        p = _Path(c)
        if p.is_file():
            return str(p)

    return None


try:
    import sounddevice as sd
    import numpy as np
    from pydub import AudioSegment
    from pydub.utils import which as pydub_which

    ffmpeg_path = _configurar_ffmpeg()
    if ffmpeg_path:
        AudioSegment.converter = ffmpeg_path
        AudioSegment.ffmpeg = ffmpeg_path
        # Tenta também o ffprobe no mesmo diretório
        ffprobe_candidate = ffmpeg_path.replace("ffmpeg.exe", "ffprobe.exe").replace("ffmpeg", "ffprobe")
        if Path(ffprobe_candidate).is_file() or ffmpeg_path.endswith("ffmpeg"):
            AudioSegment.ffprobe = ffprobe_candidate
        FFMPEG_OK = True
    elif pydub_which("ffmpeg"):
        FFMPEG_OK = True
    else:
        FFMPEG_OK = False

    TEM_MICROFONE = True
except ImportError:
    TEM_MICROFONE = False
    FFMPEG_OK = False


def obter_ip_local():
    """Descobre o IP local da máquina na rede."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def listar_musicas():
    """Retorna lista de arquivos de áudio na pasta musica."""
    if not PASTA_MUSICA.exists():
        PASTA_MUSICA.mkdir(parents=True, exist_ok=True)
        return []
    arquivos = []
    for arquivo in sorted(PASTA_MUSICA.iterdir()):
        if arquivo.is_file() and arquivo.suffix.lower() in TIPOS_SUPORTADOS:
            arquivos.append(arquivo)
    return arquivos


def montar_bloco_icy(titulo: str) -> bytes:
    """Monta um bloco de metadados ICY com o título da faixa."""
    titulo_limpo = titulo.replace("'", " ").replace("\n", " ").replace("\r", " ")[:200]
    meta = f"StreamTitle='{titulo_limpo}';".encode("utf-8", errors="replace")
    n = (len(meta) + 15) // 16
    if n > 255:
        n = 255
        meta = meta[: 255 * 16]
    padding = b"\x00" * (n * 16 - len(meta))
    return bytes([n]) + meta + padding


# ---------------------------------------------------------------------------
# Gravação do microfone (tecla R)
# ---------------------------------------------------------------------------
def gravar_anuncio():
    """
    Grava o microfone enquanto a tecla R estiver pressionada (ou por no máximo 30 s).
    Converte para MP3 e coloca na fila de anúncios para todos os ouvintes.
    """
    global gravando
    if not TEM_MICROFONE:
        print("  [DJ] Microfone indisponível. Instale: pip install sounddevice numpy pydub")
        return
    if not FFMPEG_OK:
        print("  [DJ] ffmpeg não encontrado. O anúncio não pode ser convertido para MP3.")
        print("       Veja as instruções no final deste arquivo ou no LEIA-ME.txt")
        return

    taxa = 44100
    canais = 1
    print("\n  🎤  [DJ] GRAVANDO... fale agora. Solte a tecla R para parar.")
    with lock_gravacao:
        gravando = True

    frames = []
    try:
        # Grava em blocos de 0,2 s até a tecla ser solta ou 30 s
        inicio = time.time()
        while True:
            bloco = sd.rec(int(0.2 * taxa), samplerate=taxa, channels=canais, dtype="float32")
            sd.wait()
            frames.append(bloco.copy())

            # Verifica se ainda está pressionada (a thread de teclado cuida da flag)
            with lock_gravacao:
                if not gravando:
                    break
            if time.time() - inicio > 30:
                print("  [DJ] Tempo máximo de 30 s atingido.")
                break
    except Exception as e:
        print(f"  [DJ] Erro na gravação: {e}")
        with lock_gravacao:
            gravando = False
        return

    with lock_gravacao:
        gravando = False

    if not frames:
        print("  [DJ] Nada gravado.")
        return

    print("  [DJ] Processando anúncio...")
    try:
        audio_np = np.concatenate(frames, axis=0)
        # Converte float32 (-1..1) para int16
        audio_int16 = (audio_np * 32767).astype(np.int16)

        # Cria AudioSegment e exporta como MP3 em memória
        segmento = AudioSegment(
            audio_int16.tobytes(),
            frame_rate=taxa,
            sample_width=2,
            channels=canais,
        )
        segmento = segmento.normalize()

        # Exporta para um buffer em memória (BytesIO)
        import io
        buffer = io.BytesIO()
        segmento.export(buffer, format="mp3", bitrate="128k")
        dados_mp3 = buffer.getvalue()

        # Coloca uma cópia para cada cliente futuro. Como não sabemos quantos
        # clientes existem, colocamos várias cópias (até 20) e o excesso
        # é simplesmente ignorado se não houver tantos ouvintes.
        for _ in range(20):
            fila_anuncios.put(dados_mp3)

        print(f"  [DJ] Anúncio pronto ({len(dados_mp3)//1024} KB)! Será ouvido por todos em instantes.")
    except Exception as e:
        print(f"  [DJ] Erro ao processar áudio: {e}")


def thread_teclado():
    """
    Monitora a tecla R no terminal.
    - Pressionar R → inicia gravação
    - Soltar R → para gravação e envia o anúncio
    Funciona no Windows com msvcrt; em outros sistemas usa input simples.
    """
    global gravando

    if not TEM_MICROFONE:
        return

    print("  [DJ] Pressione e segure a tecla R para falar no microfone.")
    print("       Solte a tecla R para terminar o anúncio.\n")

    # Windows
    if sys.platform == "win32":
        try:
            import msvcrt
            while True:
                if msvcrt.kbhit():
                    tecla = msvcrt.getch()
                    # R ou r
                    if tecla in (b"r", b"R"):
                        with lock_gravacao:
                            if not gravando:
                                # Inicia gravação em outra thread para não travar o teclado
                                t = threading.Thread(target=gravar_anuncio, daemon=True)
                                t.start()
                                # Espera a tecla ser solta (aproximação: espera próxima tecla ou timeout)
                                # msvcrt não tem evento de "keyup" fácil, então usamos Enter ou segunda R
                                print("  [DJ] (Pressione R novamente ou Enter para parar a gravação)")
                                while True:
                                    if msvcrt.kbhit():
                                        t2 = msvcrt.getch()
                                        if t2 in (b"r", b"R", b"\r", b"\n"):
                                            with lock_gravacao:
                                                gravando = False
                                            break
                                    time.sleep(0.05)
                                    with lock_gravacao:
                                        if not gravando:
                                            break
                time.sleep(0.05)
        except Exception as e:
            print(f"  [DJ] Erro no monitor de teclado (Windows): {e}")
    else:
        # Linux / macOS – modo simples: digite R + Enter para começar/parar
        print("  [DJ] Neste sistema digite R e pressione Enter para gravar.")
        print("       Digite R e Enter novamente para parar.\n")
        while True:
            try:
                linha = input().strip().lower()
                if linha == "r":
                    with lock_gravacao:
                        if not gravando:
                            t = threading.Thread(target=gravar_anuncio, daemon=True)
                            t.start()
                        else:
                            gravando = False
            except EOFError:
                break
            except Exception:
                time.sleep(0.5)


# ---------------------------------------------------------------------------
# Handler HTTP
# ---------------------------------------------------------------------------
class RadioHandler(BaseHTTPRequestHandler):
    """Manipulador HTTP multi-thread."""

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]}")

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])

        if path in ("/", "/index.html", "/radio"):
            self.servir_pagina()
        elif path in ("/stream", "/stream.mp3", "/radio.mp3"):
            self.servir_stream()
        elif path in ("/playlist.m3u", "/playlist.m3u8"):
            self.servir_playlist_m3u()
        elif path == "/status":
            self.servir_status()
        elif path.startswith("/arquivo/"):
            nome = path[len("/arquivo/"):]
            self.servir_arquivo_individual(nome)
        else:
            self.send_error(404, "Página não encontrada")

    def servir_pagina(self):
        ip = obter_ip_local()
        musicas = listar_musicas()
        lista_html = ""
        if musicas:
            for m in musicas:
                lista_html += f"<li>{m.name}</li>\n"
        else:
            lista_html = "<li><em>Nenhuma música encontrada. Coloque arquivos MP3 na pasta 'musica'.</em></li>"

        status_dj = "disponível (tecla R)" if TEM_MICROFONE else "indisponível (instale as bibliotecas)"

        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rádio Local</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            color: #e8e8e8;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .card {{
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            max-width: 540px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }}
        h1 {{
            font-size: 2.2rem;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #e94560, #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: #aaa; margin-bottom: 30px; font-size: 0.95rem; }}
        audio {{ width: 100%; margin: 20px 0; border-radius: 12px; }}
        .info {{
            background: rgba(0,0,0,0.25);
            border-radius: 12px;
            padding: 16px;
            margin-top: 20px;
            text-align: left;
            font-size: 0.9rem;
        }}
        .info h3 {{ margin-bottom: 10px; color: #e94560; }}
        ul {{ list-style: none; max-height: 140px; overflow-y: auto; }}
        li {{ padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .url {{
            background: #0f3460;
            padding: 10px 14px;
            border-radius: 8px;
            font-family: monospace;
            word-break: break-all;
            margin: 12px 0;
            display: block;
        }}
        .status {{ color: #4ade80; font-weight: 600; }}
        .dica {{ margin-top: 12px; font-size: 0.85rem; color: #94a3b8; line-height: 1.45; }}
        .dj {{ color: #fbbf24; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>📻 Rádio Local</h1>
        <p class="subtitle">Streaming na sua rede local</p>
        
        <audio controls autoplay>
            <source src="/stream" type="audio/mpeg">
            Seu navegador não suporta o elemento de áudio.
        </audio>
        
        <p class="status">● AO VIVO</p>
        
        <div class="info">
            <h3>Como ouvir em outros dispositivos</h3>
            <p>Na mesma rede Wi-Fi, abra:</p>
            <span class="url">http://{ip}:{PORTA}</span>
            <p class="dica">
                <strong>Modo Rádio (stream contínuo):</strong><br>
                VLC → Mídia → Abrir Fluxo de Rede →<br>
                <code>http://{ip}:{PORTA}/stream</code>
            </p>
            <p class="dica">
                <strong>Modo Playlist (próximo/anterior):</strong><br>
                VLC → Mídia → Abrir Fluxo de Rede →<br>
                <code>http://{ip}:{PORTA}/playlist.m3u</code>
            </p>
        </div>
        
        <div class="info">
            <h3 class="dj">🎤 Modo DJ (falar ao vivo)</h3>
            <p class="dica">
                No computador do servidor, pressione e segure a tecla <strong>R</strong>
                para gravar um anúncio pelo microfone. Ao soltar, o anúncio é
                transmitido para <strong>todos</strong> os ouvintes, interrompendo a música.
            </p>
            <p class="dica">Status do microfone: <strong>{status_dj}</strong></p>
        </div>
        
        <div class="info">
            <h3>Playlist atual ({len(musicas)} faixas)</h3>
            <ul>
                {lista_html}
            </ul>
        </div>
    </div>
</body>
</html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def servir_status(self):
        import json
        musicas = listar_musicas()
        data = {
            "status": "ao_vivo",
            "musicas": [m.name for m in musicas],
            "total": len(musicas),
            "porta": PORTA,
            "microfone": TEM_MICROFONE,
            "gravando": gravando,
        }
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def servir_playlist_m3u(self):
        musicas = listar_musicas()
        ip = obter_ip_local()
        linhas = ["#EXTM3U"]
        for m in musicas:
            linhas.append(f"#EXTINF:-1,{m.stem}")
            nome_enc = urllib.parse.quote(m.name)
            linhas.append(f"http://{ip}:{PORTA}/arquivo/{nome_enc}")
        conteudo = "\n".join(linhas) + "\n"
        body = conteudo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "audio/x-mpegurl; charset=utf-8")
        self.send_header("Content-Disposition", "inline; filename=\"playlist.m3u\"")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        print(f"  → Playlist M3U enviada para {self.client_address[0]} ({len(musicas)} faixas)")

    def servir_arquivo_individual(self, nome: str):
        nome = Path(nome).name
        caminho = PASTA_MUSICA / nome
        if not caminho.is_file() or caminho.suffix.lower() not in TIPOS_SUPORTADOS:
            self.send_error(404, "Arquivo não encontrado")
            return
        try:
            tamanho = caminho.stat().st_size
            ext = caminho.suffix.lower()
            content_types = {
                ".mp3": "audio/mpeg",
                ".ogg": "audio/ogg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".flac": "audio/flac",
            }
            ctype = content_types.get(ext, "application/octet-stream")
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(tamanho))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            print(f"  → Enviando arquivo: {nome} → {self.client_address[0]}")
            with open(caminho, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            print(f"  → Cliente desconectou durante envio de {nome}")
        except Exception as e:
            print(f"  → Erro ao enviar {nome}: {e}")

    def _enviar_dados_no_stream(self, dados, quer_icy: bool, titulo: str, bytes_desde_meta: list):
        """
        Envia dados de áudio (bytes de um MP3 ou arquivo aberto) dentro do stream.
        'dados' pode ser bytes (anúncio) ou um Path (música).
        """
        desconexao = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError)
        try:
            if isinstance(dados, (bytes, bytearray)):
                # Anúncio em memória
                offset = 0
                total = len(dados)
                while offset < total:
                    if quer_icy:
                        falta = ICY_META_INTERVAL - bytes_desde_meta[0]
                        tamanho = min(16384, falta, total - offset)
                    else:
                        tamanho = min(16384, total - offset)
                    chunk = dados[offset:offset + tamanho]
                    offset += tamanho
                    self.wfile.write(chunk)
                    self.wfile.flush()
                    if quer_icy:
                        bytes_desde_meta[0] += len(chunk)
                        if bytes_desde_meta[0] >= ICY_META_INTERVAL:
                            meta = montar_bloco_icy(titulo)
                            self.wfile.write(meta)
                            self.wfile.flush()
                            bytes_desde_meta[0] = 0
            else:
                # Arquivo em disco (música)
                with open(dados, "rb") as f:
                    while True:
                        if quer_icy:
                            falta = ICY_META_INTERVAL - bytes_desde_meta[0]
                            chunk = f.read(min(16384, falta))
                        else:
                            chunk = f.read(16384)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        if quer_icy:
                            bytes_desde_meta[0] += len(chunk)
                            if bytes_desde_meta[0] >= ICY_META_INTERVAL:
                                meta = montar_bloco_icy(titulo)
                                self.wfile.write(meta)
                                self.wfile.flush()
                                bytes_desde_meta[0] = 0
        except desconexao:
            raise

    def servir_stream(self):
        """Stream contínuo com suporte a inserção de anúncios do DJ."""
        musicas = listar_musicas()
        if not musicas:
            self.send_response(503)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"Nenhuma musica encontrada. Coloque arquivos .mp3 na pasta 'musica'."
            )
            return

        quer_icy = self.headers.get("Icy-MetaData", "0") == "1"

        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Cache-Control", "no-cache, no-store")
        self.send_header("Pragma", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("icy-name", "Radio Local")
        self.send_header("icy-genre", "Variado")
        self.send_header("icy-pub", "0")
        self.send_header("Accept-Ranges", "none")
        if quer_icy:
            self.send_header("icy-metaint", str(ICY_META_INTERVAL))
        self.end_headers()

        print(f"  → Cliente conectado ao stream: {self.client_address[0]}")

        desconexao = (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError)
        bytes_desde_meta = [0]  # lista para poder alterar dentro da função auxiliar

        try:
            while True:
                # 1) Verifica se existe anúncio pendente do DJ
                try:
                    while True:
                        anuncio_bytes = fila_anuncios.get_nowait()
                        print(f"  → [{self.client_address[0]}] 🎤 ANÚNCIO DO DJ")
                        self._enviar_dados_no_stream(
                            anuncio_bytes, quer_icy, "Anúncio ao vivo - Rádio Local", bytes_desde_meta
                        )
                except queue.Empty:
                    pass

                # 2) Toca a próxima música da playlist
                for musica in musicas:
                    # Verifica anúncios entre as músicas também
                    try:
                        while True:
                            anuncio_bytes = fila_anuncios.get_nowait()
                            print(f"  → [{self.client_address[0]}] 🎤 ANÚNCIO DO DJ")
                            self._enviar_dados_no_stream(
                                anuncio_bytes, quer_icy, "Anúncio ao vivo - Rádio Local", bytes_desde_meta
                            )
                    except queue.Empty:
                        pass

                    print(f"  → [{self.client_address[0]}] Tocando: {musica.name}")
                    self._enviar_dados_no_stream(
                        musica, quer_icy, musica.stem, bytes_desde_meta
                    )

                time.sleep(0.15)
        except desconexao:
            print(f"  → Cliente desconectou: {self.client_address[0]}")
        except Exception as e:
            print(f"  → Erro no stream: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    global PORTA

    if len(sys.argv) > 1:
        try:
            PORTA = int(sys.argv[1])
        except ValueError:
            print("Porta inválida. Use um número, exemplo: python radio_server.py 8080")
            sys.exit(1)

    ip = obter_ip_local()
    musicas = listar_musicas()

    print("=" * 60)
    print("  📻  RÁDIO LOCAL - Servidor de Streaming (Multi-cliente + DJ)")
    print("=" * 60)
    print(f"  Endereço local      : http://{ip}:{PORTA}")
    print(f"  Stream contínuo     : http://{ip}:{PORTA}/stream")
    print(f"  Playlist (VLC)      : http://{ip}:{PORTA}/playlist.m3u")
    print(f"  Pasta de músicas    : {PASTA_MUSICA}")
    print(f"  Faixas encontradas  : {len(musicas)}")
    if musicas:
        for m in musicas:
            print(f"    • {m.name}")
    else:
        print("  ⚠  Nenhuma música encontrada!")
        print("     Coloque arquivos MP3 na pasta 'musica' e reinicie.")
    print("-" * 60)

    if TEM_MICROFONE and FFMPEG_OK:
        print("  🎤  Modo DJ ATIVO")
        print("      Pressione a tecla R para falar no microfone.")
        print("      Pressione R novamente (ou Enter) para enviar o anúncio.")
        t_teclado = threading.Thread(target=thread_teclado, daemon=True)
        t_teclado.start()
    elif TEM_MICROFONE and not FFMPEG_OK:
        print("  🎤  Modo DJ PARCIALMENTE INATIVO")
        print("      Bibliotecas Python OK, mas o ffmpeg NÃO foi encontrado.")
        print()
        print("      Como corrigir no Windows:")
        print("      1. Baixe o ffmpeg em: https://www.gyan.dev/ffmpeg/builds/")
        print("         (escolha 'ffmpeg-release-essentials.zip')")
        print("      2. Extraia para C:\\ffmpeg")
        print("      3. A pasta C:\\ffmpeg\\bin deve conter o arquivo ffmpeg.exe")
        print("      4. Adicione C:\\ffmpeg\\bin ao PATH do sistema")
        print("      5. FECHE e ABRA novamente o Prompt de Comando / PowerShell")
        print("      6. Teste digitando:  ffmpeg -version")
        print("      7. Depois rode de novo:  python radio_server.py")
        print()
        print("      Alternativa rápida (sem PATH):")
        print("      Coloque o ffmpeg.exe na mesma pasta deste script.")
    else:
        print("  🎤  Modo DJ INATIVO")
        print("      Para ativar, instale as bibliotecas:")
        print("          pip install sounddevice numpy pydub")
        print("      E tenha o ffmpeg instalado (veja instruções no LEIA-ME).")
    print("-" * 60)
    print("  Vários dispositivos podem ouvir ao mesmo tempo.")
    print("  Pressione Ctrl+C para parar o servidor.")
    print("=" * 60)

    ThreadingHTTPServer.allow_reuse_address = True
    servidor = ThreadingHTTPServer(("0.0.0.0", PORTA), RadioHandler)

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor encerrado.")
        servidor.server_close()
    except OSError as e:
        if getattr(e, "errno", None) in (98, 10048):
            print(f"\n  ERRO: A porta {PORTA} já está em uso.")
            print(f"  Tente outra porta: python radio_server.py {PORTA + 1}")
        else:
            print(f"\n  Erro ao iniciar o servidor: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
