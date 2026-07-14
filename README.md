# ⚖️ Assistente RAG — Reforma Tributária (IBS/CBS)

> Assistente conversacional baseado em IA para consulta semântica ao Regulamento do IBS (Resolução CGIBS Nº 6/2026).  
> Projeto acadêmico desenvolvido com Python, Google Gemini, Supabase e Streamlit.
> Desenvolvido por prof. Rômulo Negi Camargo. Autorizado uso para alunos da EBPOs.

---

## 📌 Sobre o Projeto

Este sistema implementa a técnica de **RAG (Retrieval-Augmented Generation)** para permitir que profissionais e estudantes façam perguntas em linguagem natural sobre a legislação do IBS, recebendo respostas fundamentadas **exclusivamente nos artigos oficiais da Resolução**, com citação explícita das fontes.

O problema central que resolve: a lei tem 617 artigos em um PDF denso e hierárquico. A busca por palavras-chave é insuficiente para capturar o contexto jurídico. O RAG permite que a IA encontre os artigos semanticamente relevantes e componha uma resposta precisa e rastreável.

---

## 🏗️ Arquitetura

O projeto é dividido em **3 etapas sequenciais**, executadas uma única vez, mais a **interface** que roda continuamente:

```
[Notebook 1]          [Notebook 2]           [Streamlit]
PDF da Resolução  →   Vetorização       →    Interface RAG
      │               + Ingestão              Conversacional
      │               Supabase                    │
      ▼                   │                       ▼
  JSON estruturado         └──────────────▶  Busca Semântica
  (artigo por artigo)          banco            + Gemini
                              vetorial           responde
```

### Tech Stack

| Camada | Tecnologia |
|---|---|
| Extração de PDF | `pdfplumber` + `re` (Regex) — Google Colab |
| Banco Vetorial | Supabase (PostgreSQL + `pgvector`) |
| Embeddings | `gemini-embedding-2` — 3072 dimensões |
| Geração de Texto | `gemini-2.5-flash` |
| Interface | Streamlit |
| Hospedagem | Streamlit Community Cloud |

---

## 📁 Estrutura do Repositório

```
📦 ragcoelhosabido/
├── app.py                          # Interface RAG (Streamlit)
├── requirements.txt                # Dependências Python para o Streamlit Cloud
├── README.md                       # Este arquivo
├── .gitignore                      # Ignora secrets e arquivos gerados
│
├── .streamlit/
│   └── secrets.toml.example        # Template de configuração de credenciais
│
└── docs/
    ├── PRD.md                      # Product Requirements Document
    └── SPEC.md                     # Technical Specification
```

> Os Notebooks do Google Colab (Etapas 1 e 2) são executados separadamente  
> e não precisam estar no repositório do Streamlit.

---

## 🚀 Como Usar

### Pré-requisitos

Antes de começar, você precisará de:

- [ ] Conta no **Google** com acesso ao [Google Colab](https://colab.research.google.com)
- [ ] Conta no **Supabase** (gratuita) — [supabase.com](https://supabase.com)
- [ ] **Chave de API do Google Gemini** — [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- [ ] Conta no **GitHub** (para o deploy no Streamlit Cloud)
- [ ] Arquivo PDF da **Resolução CGIBS Nº 6/2026**

---

### Etapa 1 — Extrair e Estruturar o PDF

Execute o **Notebook 1** no Google Colab:

1. Abra o `Notebook_1_Extracao.ipynb` no Colab
2. Execute todas as células em ordem
3. Faça o upload do PDF quando solicitado
4. Ao final, baixe o arquivo `regulamento_ibs_pronto_para_rag.json`

---

### Etapa 2 — Configurar o Banco de Dados (Supabase)

#### 2.1 Criar conta e projeto
1. Acesse [supabase.com](https://supabase.com) e crie uma conta
2. Crie um novo projeto em **South America (São Paulo)**
3. Aguarde ~2 minutos até o projeto ficar ativo

#### 2.2 Executar o script SQL
1. No painel do Supabase, acesse **SQL Editor** (`</>`)
2. Clique em **New query**
3. Cole o conteúdo do arquivo `setup_supabase.sql` (disponível nos arquivos de suporte do projeto)
4. Clique em **Run** — resultado esperado: `Success. No rows returned`

#### 2.3 Coletar credenciais
No Supabase, vá em **Project Settings > API** e copie:
- **Project URL**: `https://xxxxxxxxxxxx.supabase.co`
- **service_role** key (em "Project API Keys")

---

### Etapa 3 — Vetorizar e Gravar no Banco

Execute o **Notebook 2** no Google Colab:

1. Abra o `Notebook_2_Vetorizacao_Supabase.ipynb` no Colab
2. Execute todas as células em ordem
3. Insira suas credenciais quando solicitado (campos ocultos)
4. O notebook verificará a estrutura do banco antes de gravar
5. Aguarde o processamento dos 617 artigos (~5 minutos)

---

### Etapa 4 — Deploy no Streamlit Cloud

#### 4.1 Subir o código para o GitHub
1. Crie um repositório público no GitHub
2. Suba os arquivos: `app.py`, `requirements.txt` e a pasta `docs/`

#### 4.2 Conectar ao Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io) com sua conta Google
2. Clique em **"New app"**
3. Conecte ao repositório GitHub
4. Em **"Advanced settings"**, configure os **Secrets**:

```toml
SUPABASE_URL   = "https://xxxxxxxxxxxx.supabase.co"
SUPABASE_KEY   = "eyJ..."
GOOGLE_API_KEY = "AIza..."
```

5. Clique em **"Deploy!"**

---

## 🔑 Configuração de Credenciais

O `app.py` suporta dois modos automaticamente:

| Modo | Como funciona |
|---|---|
| **Produção** (Streamlit Cloud) | Lê de `st.secrets` — configure na UI do Streamlit Cloud |
| **Demonstração local** | Exibe campos na barra lateral da interface |

Para uso local com `streamlit run app.py`:
1. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`
2. Preencha com suas chaves reais
3. O `secrets.toml` está no `.gitignore` e nunca será enviado ao GitHub

---

## 💬 Como Funciona a Busca

Cada vez que o usuário faz uma pergunta:

1. A pergunta é convertida em um vetor de **3072 dimensões** pelo `gemini-embedding-2`
2. O vetor é comparado com os vetores dos 617 artigos no banco (distância do cosseno)
3. Os **4 artigos mais relevantes** com similaridade acima de **30%** são recuperados
4. O `gemini-2.5-flash` formula a resposta baseando-se **exclusivamente** nesses artigos
5. A resposta é exibida com os IDs dos artigos consultados no rodapé

---

## 📚 Documentação

| Documento | Descrição |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Product Requirements Document — visão, público-alvo e casos de uso |
| [docs/SPEC.md](docs/SPEC.md) | Technical Specification — arquitetura, tech stack e parâmetros |

---

## ⚠️ Aviso Legal

Este sistema é uma ferramenta de consulta **acadêmica e de referência**. As respostas são geradas por IA com base nos artigos da Resolução CGIBS Nº 6/2026 e **não constituem parecer jurídico ou contábil**. Para decisões tributárias, consulte um profissional habilitado.

---

## 🎓 Contexto Acadêmico

Projeto desenvolvido como parte de curso de IA aplicada, demonstrando a técnica de RAG (Retrieval-Augmented Generation) aplicada a documentos jurídicos de alta complexidade.
