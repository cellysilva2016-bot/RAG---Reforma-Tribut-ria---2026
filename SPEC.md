# Technical Specification (SPEC)
## Projeto: Assistente RAG — Especialista em Reforma Tributária (IBS/CBS)

---

### 1. Arquitetura do Sistema

O projeto adota uma arquitetura de **Geração Aumentada por Recuperação (RAG)** em 4 camadas sequenciais:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARQUITETURA RAG                              │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   ETAPA 1    │    │   ETAPA 2    │    │       ETAPA 3        │  │
│  │  Extração    │───▶│  Ingestão    │    │   Interface RAG      │  │
│  │   (ETL)      │    │  Supabase    │    │     (Streamlit)      │  │
│  │              │    │              │    │                      │  │
│  │ PDF → JSON   │    │ JSON →       │    │ Pergunta → Embedding │  │
│  │ (Notebook 1) │    │ Embeddings   │    │ → Busca Semântica    │  │
│  │              │    │ → Banco      │    │ → Prompt → Resposta  │  │
│  │              │    │ (Notebook 2) │    │                      │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                    ▲                │
│                              ┌─────────────────────┘               │
│                              │   ETAPA 4 (transversal)             │
│                              │   Banco Vetorial                    │
│                              │   Supabase + pgvector               │
│                              └─────────────────────────────────────│
└─────────────────────────────────────────────────────────────────────┘
```

---

### 2. Tech Stack

| Camada | Tecnologia | Função |
|---|---|---|
| ETL / Extração | Python 3 (Google Colab) + `pdfplumber` + `re` | Leitura hierárquica do PDF |
| Banco de Dados Vetorial | Supabase (PostgreSQL + extensão `pgvector`) | Armazenamento e busca semântica |
| Modelo de Embedding | `gemini-embedding-2` via `google-genai` SDK | Vetorização dos artigos e perguntas |
| Modelo de Geração | `gemini-2.5-flash` via `google-genai` SDK | Geração da resposta final |
| Frontend | Streamlit 1.x | Interface conversacional |
| Hospedagem | Streamlit Community Cloud | Deploy gratuito via GitHub |

---

### 3. Estratégia de Chunking (Fragmentação)

- **Unidade semântica:** 1 chunk = 1 Artigo completo da lei
- **Justificativa:** Artigos são a unidade mínima de significado jurídico autônomo. Fragmentar em parágrafos perderia o contexto do caput; agregar por capítulos excederia o limite de tokens úteis.
- **Metadados preservados:** Cada chunk carrega sua árvore hierárquica completa:

```json
{
  "id": "Artigo_156",
  "metadata": {
    "livro":    "LIVRO I - DAS NORMAS COMUNS AO IBS E À CBS",
    "titulo":   "TÍTULO VI - DOS REGIMES ESPECÍFICOS",
    "capitulo": "CAPÍTULO II - DOS SERVIÇOS FINANCEIROS",
    "secao":    "Seção I - Da Incidência",
    "subsecao": ""
  },
  "page_content": "Art. 156º ..."
}
```

---

### 4. Estrutura do Banco de Dados

**Tabela:** `regulamento_ibs`

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | `TEXT` (PK) | Identificador único — ex: `"Artigo_1"` |
| `metadata` | `JSONB` | Árvore hierárquica do artigo |
| `page_content` | `TEXT` | Texto integral do artigo |
| `embedding` | `VECTOR(3072)` | Representação vetorial gerada pelo Gemini |

**Função de busca:** `buscar_artigos_ibs(query_embedding, match_threshold, match_count)`
- Algoritmo: distância do cosseno (`<=>` do pgvector)
- Retorno: artigos ordenados por similaridade decrescente

---

### 5. Dimensionalidade dos Vetores

O modelo `gemini-embedding-2` é configurado com `output_dimensionality: 3072`, produzindo **embeddings densos de alta dimensão** (high-density embeddings). Esta configuração:

- Captura nuances semânticas do jargão jurídico-tributário com maior precisão
- É fixada explicitamente em todas as chamadas à API (embedding e busca) para garantir consistência dimensional
- Corresponde ao tipo `VECTOR(3072)` declarado no banco

---

### 6. Fluxo de Execução da Interface RAG

```
Usuário digita pergunta
        │
        ▼
[A] Embedding da pergunta
    gemini-embedding-2 → vetor de 3072 dimensões
        │
        ▼
[B] Busca semântica no Supabase
    RPC buscar_artigos_ibs(vetor, threshold=0.3, top_k=4)
    Distância do cosseno → Top 4 artigos mais relevantes
        │
        ├── Nenhum artigo acima do threshold → mensagem de "não encontrado"
        │
        ▼
[C] Montagem do contexto
    Concatena: id + hierarquia + page_content de cada artigo
        │
        ▼
[D] Construção do prompt
    System: especialista tributário, citar fontes, não alucinar
    Context: trechos dos artigos recuperados
    Query: pergunta original do usuário
        │
        ▼
[E] Geração da resposta
    gemini-2.5-flash → texto fundamentado nos artigos
        │
        ▼
[F] Exibição com rodapé de referências
    Resposta + "Artigos consultados: Artigo_X, Artigo_Y"
```

---

### 7. Gerenciamento de Credenciais

| Contexto | Mecanismo | Arquivo |
|---|---|---|
| Streamlit Cloud (produção) | `st.secrets` | Configurado na UI do Streamlit Cloud |
| Desenvolvimento local | `st.secrets` | `.streamlit/secrets.toml` (no `.gitignore`) |
| Demonstração sem deploy | Sidebar da interface | Campos `type="password"` no `app.py` |
| Notebooks Colab | `getpass.getpass()` | Entrada oculta em tempo de execução |

---

### 8. Parâmetros de Configuração

| Parâmetro | Valor | Localização |
|---|---|---|
| `match_threshold` | `0.3` (30%) | `app.py` — busca semântica |
| `match_count` | `4` (Top 4) | `app.py` — busca semântica |
| `output_dimensionality` | `3072` | `app.py` e `Notebook_2` |
| `TAMANHO_LOTE` | `20` artigos | `Notebook_2` — ingestão |
| `PAUSA_LOTE` | `2` segundos | `Notebook_2` — rate limit API |
| Embedding model | `gemini-embedding-2` | `app.py` e `Notebook_2` |
| Generation model | `gemini-2.5-flash` | `app.py` |
