# 📻 RadioLocal

Rádio local em Python para transmitir música em rede local, permitindo que vários dispositivos escutem ao mesmo tempo usando o mesmo servidor.

Este projeto cria um servidor web simples que gera um stream contínuo de áudio a partir de arquivos na pasta `musica/`, além de oferecer uma playlist em formato M3U para uso em VLC ou outros players.

## ✨ Funcionalidades

- Streaming contínuo em rede local
- Suporte a vários ouvintes simultaneamente
- Playlist em formato M3U
- Reprodução de arquivos em formatos como `.mp3`, `.ogg`, `.wav`, `.m4a` e `.flac`
- Interface web simples para ouvir no navegador
- Modo DJ opcional com microfone: pressione e segure a tecla `R` para interromper a música e anunciar ao vivo
- Funciona com Windows, Linux e macOS

## 🧩 Estrutura do projeto

```text
RadioLocal/
├── radio_server.py        # Servidor principal da rádio
├── iniciar_radio.bat      # Script para Windows
├── iniciar_radio.sh       # Script para Linux/macOS
├── musica/                # Cole aqui suas músicas
├── LEIA-ME.txt            # Instruções rápidas
├── LICENSE                # Licença do projeto
├── README.md              # Documentação do projeto
└── .github/               # Configurações do GitHub
```

## 🚀 Como usar

### 1) Coloque suas músicas

Crie ou abra a pasta `musica/` e adicione seus arquivos de áudio dentro dela.

Exemplo:

```text
musica/
├── rock.mp3
├── eletronica.mp3
├── podcast.wav
└── mix.flac
```

### 2) Inicie o servidor

#### Windows

- Clique duas vezes no arquivo `iniciar_radio.bat`, ou
- Abra o terminal e execute:

```bash
python radio_server.py
```

#### Linux/macOS

```bash
python3 radio_server.py
```

Você também pode escolher uma porta diferente:

```bash
python radio_server.py 8080
```

### 3) Acesse a rádio

O servidor exibirá um endereço local semelhante a este:

```text
http://192.168.0.15:7074
```

A partir daí, você pode acessar:

- `http://SEU_IP:7074/` → página web da rádio
- `http://SEU_IP:7074/stream` → stream contínuo da rádio
- `http://SEU_IP:7074/playlist.m3u` → playlist para VLC
- `http://SEU_IP:7074/status` → status em JSON do servidor

## 🎧 Como ouvir

### No navegador

Abra o endereço exibido pelo servidor no navegador, por exemplo:

```text
http://192.168.0.15:7074
```

### No VLC

1. Abra o VLC
2. Vá em `Mídia` → `Abrir Fluxo de Rede`
3. Cole uma das URLs abaixo:

```text
http://SEU_IP:7074/stream
```

Ou para uma playlist com faixa separada:

```text
http://SEU_IP:7074/playlist.m3u
```

## 🎤 Modo DJ (microfone)

Se quiser anunciar ao vivo para todos os ouvintes:

- Instale as dependências opcionais:

```bash
pip install sounddevice numpy pydub
```

- Instale também o `ffmpeg` e deixe-o acessível no `PATH` do sistema
- No computador que está executando o servidor, pressione e segure a tecla `R`
- Quando soltar, o áudio do microfone será convertido e transmitido para todos os ouvintes

> O modo DJ só funciona corretamente quando o `ffmpeg` estiver instalado e configurado.

## 🧪 Requisitos

### Básico

- Python 3.7 ou superior

### Opcional para microfone/DJ

- `sounddevice`
- `numpy`
- `pydub`
- `ffmpeg`

## ⚠️ Solução de problemas

### Porta já em uso

Se a porta estiver ocupada, execute:

```bash
python radio_server.py 8080
```

### Nenhuma música encontrada

Verifique se:

- a pasta `musica/` existe
- há arquivos de áudio válidos dentro dela
- os arquivos têm extensão suportada

### Microfone não funciona

Confirme se:

- as bibliotecas foram instaladas
- o `ffmpeg` está instalado e no `PATH`
- o sistema reconhece o microfone

## 📜 Licença

Este projeto está licenciado sob a licença contida no arquivo `LICENSE`.

## 🔗 Informações

Projeto: `JPpixelado/RadioLocal`

Desenvolvido com Python para criação de rádio local em rede Wi‑Fi/LAN.
