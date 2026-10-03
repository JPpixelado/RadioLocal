# 🤝 Guia de Contribuição - RadioLocal

Obrigado por se interessar em contribuir para o **RadioLocal**! Este documento ajudará você a entender como participar do projeto.

## 📋 Índice

1. [Antes de Começar](#antes-de-começar)
2. [Tipos de Contribuições](#tipos-de-contribuições)
3. [Como Configurar o Ambiente](#como-configurar-o-ambiente)
4. [Processo de Submissão](#processo-de-submissão)
5. [Padrões de Código](#padrões-de-código)
6. [Reportando Bugs](#reportando-bugs)
7. [Sugerindo Melhorias](#sugerindo-melhorias)
8. [Perguntas?](#perguntas)

---

## Antes de Começar

- Leia o [README.md](README.md) para entender o projeto
- Verifique as [Issues](../../issues) existentes para não duplicar trabalho
- Familiarize-se com a estrutura do projeto

---

## Tipos de Contribuições

### 🐛 Correção de Bugs
Encontrou um problema? Abra uma issue ou submeta um pull request com a correção.

### ✨ Novas Funcionalidades
Tem uma ideia legal? Abra uma issue para discutir antes de começar a trabalhar.

### 📖 Documentação
Melhorias no README, documentação de código ou tutoriais são sempre bem-vindos.

### 🧪 Testes
Ajude a melhorar a cobertura de testes do projeto.

### 🎨 Melhorias de Interface
Sugestões para a interface web ou experiência do usuário.

---

## Como Configurar o Ambiente

### Pré-requisitos

- **Python 3.7+** instalado
- **Git** instalado
- Uma conta no **GitHub**

### Passo 1: Faça um Fork do Repositório

1. Vá até https://github.com/JPpixelado/RadioLocal
2. Clique no botão **Fork** no canto superior direito
3. Selecione sua conta pessoal

### Passo 2: Clone o Repositório

```bash
# Clone seu fork
git clone https://github.com/SEU_USUARIO/RadioLocal.git

# Entre na pasta do projeto
cd RadioLocal

# Adicione o repositório original como upstream
git remote add upstream https://github.com/JPpixelado/RadioLocal.git
```

### Passo 3: Crie uma Branch para sua Contribuição

```bash
# Atualize a branch main
git fetch upstream
git checkout main
git merge upstream/main

# Crie uma nova branch com um nome descritivo
git checkout -b nome-da-sua-feature
# Exemplos: fix/corrige-stream, feature/modo-dj-melhorado, docs/tutorial
```

### Passo 4: Configure as Dependências (Opcional)

Para testar todas as funcionalidades, instale as dependências opcionais:

```bash
# Dependências básicas (se necessário)
pip install -r requirements.txt

# Dependências opcionais (para modo DJ)
pip install sounddevice numpy pydub
```

---

## Processo de Submissão

### Passo 1: Faça suas Alterações

- Edite os arquivos necessários
- Teste suas mudanças localmente
- Certifique-se de que não quebrou nada

```bash
# Para testar o servidor
python radio_server.py

# O servidor rodará em http://localhost:7074 por padrão
```

### Passo 2: Commit suas Mudanças

```bash
# Veja as mudanças
git status

# Adicione os arquivos modificados
git add .

# Faça o commit com uma mensagem clara e descritiva
git commit -m "Descrição clara do que foi mudado"
```

**Dicas para boas mensagens de commit:**
- Use o imperativo: "Add feature" em vez de "Added feature"
- Seja descritivo mas conciso
- Referencie issues se aplicável: "Fix #123"

Exemplos:
```
Add DJ mode improvement for better audio quality
Fix stream connection timeout issue
Update documentation for Linux setup
Refactor audio streaming handler
```

### Passo 3: Envie para seu Fork

```bash
git push origin nome-da-sua-feature
```

### Passo 4: Abra um Pull Request

1. Vá para https://github.com/JPpixelado/RadioLocal
2. Clique em "Compare & pull request" (deve aparecer um banner)
3. **Título:** Descrição clara e concisa
4. **Descrição:** Inclua:
   - O que foi mudado e por quê
   - Como testar as mudanças
   - Se fecha alguma issue, use: `Closes #numero`
   - Screenshots ou vídeos (se aplicável)

**Template de Pull Request:**

```markdown
## Descrição
Breve descrição do que este PR faz.

## Tipo de Mudança
- [ ] Bug fix
- [ ] Nova funcionalidade
- [ ] Melhoria de documentação
- [ ] Refatoração de código

## Mudanças
- Ponto 1
- Ponto 2
- Ponto 3

## Como Testar
Instruções passo a passo para testar as mudanças.

## Checklist
- [ ] Meu código segue o estilo do projeto
- [ ] Testei localmente as mudanças
- [ ] Atualizei a documentação (se necessário)
- [ ] Não há conflitos com a branch principal

## Screenshots (se aplicável)
[Adicione aqui]

Closes #(issue number)
```

---

## Padrões de Código

### Python Style Guide

Seguimos as convenções do **PEP 8**:

```python
# ✅ BOM
def transmit_audio_stream(port=7074):
    """Transmit audio stream on specified port."""
    server = AudioServer(port)
    server.start()
    return server

# ❌ RUIM
def transmitAudioStream(p=7074):
    s=AudioServer(p)
    s.start()
    return s
```

### Estrutura de Código

- Use nomes descritivos para variáveis e funções
- Adicione docstrings para funções públicas
- Mantenha funções pequenas e focadas
- Use comentários apenas para lógica complexa

### Exemplo com Docstring

```python
def stream_audio_file(filepath, bitrate=128):
    """
    Stream an audio file at specified bitrate.
    
    Args:
        filepath (str): Path to the audio file
        bitrate (int): Bitrate in kbps (default: 128)
        
    Returns:
        bytes: Audio stream data
        
    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If bitrate is invalid
    """
    # Implementation here
    pass
```

---

## Reportando Bugs

### Quando Abrir uma Issue de Bug

1. Verifique se o bug já foi reportado
2. Fornça informações suficientes para reproduzir

### Como Reportar um Bug

Use o template abaixo ao abrir uma issue:

```markdown
## Descrição do Bug
Descrição clara do problema.

## Como Reproduzir
1. Faça isso
2. Depois aquilo
3. Observe o erro

## Comportamento Esperado
O que deveria acontecer.

## Comportamento Atual
O que realmente acontece.

## Informações do Sistema
- OS: [Windows/Linux/macOS]
- Python: [versão]
- Navegador: [se aplicável]
- Porta utilizada: [porta]

## Logs/Erros
Cole qualquer mensagem de erro ou log relevante.

## Screenshots
[Se aplicável]
```

---

## Sugerindo Melhorias

### Quando Abrir uma Issue de Sugestão

1. Verifique se a sugestão já foi feita
2. Descreva o caso de uso claro

### Como Sugerir uma Melhoria

```markdown
## Descrição da Sugestão
Descrição clara da melhoria.

## Motivo
Por que essa mudança seria útil?

## Exemplos Possíveis
Como a funcionalidade poderia ser usada?

## Contexto Adicional
Informações extras que sejam relevantes.
```

---

## Boas Práticas

### Antes de Submeter

- [ ] Testei localmente as mudanças
- [ ] Não há código duplicado
- [ ] A documentação foi atualizada
- [ ] Não há arquivos desnecessários adicionados
- [ ] Segui o padrão de código do projeto

### Após Submeter

- Responda aos comentários de revisão
- Não é esperado aceitar toda crítica, mas explique sua posição
- Seja paciente com o processo de revisão
- Obrigado por contribuir!

---

## Fluxo Resumido

```
1. Fork o repositório
   ↓
2. Clone e crie uma branch
   ↓
3. Faça as mudanças
   ↓
4. Commit com mensagens claras
   ↓
5. Push para seu fork
   ↓
6. Abra um Pull Request
   ↓
7. Responda aos comentários
   ↓
8. Merge! 🎉
```

---

## Perguntas?

- 📖 Abra uma [Discussão](../../discussions)
- 🐛 Reporte um [Bug](../../issues)
- 💡 Sugira uma [Melhoria](../../issues)

---

## Obrigado!

Sua contribuição faz o RadioLocal mais incrível! 🎵

---

**Desenvolvido com ❤️ para a comunidade de rádios locais**
