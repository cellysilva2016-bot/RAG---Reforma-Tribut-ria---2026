# ================================================================
# app.py — Assistente RAG: Reforma Tributária (IBS/CBS)
# Framework: Streamlit
# ================================================================
# DEPLOY NO STREAMLIT CLOUD:
#   1. Suba este arquivo para um repositório GitHub público
#   2. Acesse share.streamlit.io e conecte o repositório
#   3. Em "Advanced settings > Secrets", adicione:
#        SUPABASE_URL   = "https://xxx.supabase.co"
#        SUPABASE_KEY   = "eyJ..."
#        GOOGLE_API_KEY = "AIza..."
#
# USO LOCAL / DEMONSTRAÇÃO:
#   As chaves são inseridas na barra lateral da interface.
# ================================================================

import streamlit as st
from supabase import create_client
from google import genai

# ── Configuração da página ────────────────────────────────────────────────
st.set_page_config(
    page_title="Especialista Tributário IBS/CBS",
    page_icon="⚖️",
    layout="centered"
)

st.title("⚖️ Assistente RAG: Reforma Tributária (IBS/CBS)")
st.markdown(
    "Faça perguntas sobre o **Regulamento do IBS** (Resolução CGIBS Nº 6/2026). "
    "As respostas são baseadas exclusivamente nos artigos oficiais da legislação."
)
st.divider()


# ── Gerenciamento de credenciais ──────────────────────────────────────────
# ESTRATÉGIA DUPLA:
#   1ª opção: lê do st.secrets (arquivo .streamlit/secrets.toml no deploy)
#   2ª opção: exibe campos na barra lateral (demonstração local)
#
# Isso permite que o mesmo arquivo app.py funcione em ambos os contextos
# sem nenhuma alteração de código.

def obter_credenciais():
    """
    Tenta ler credenciais do st.secrets (produção no Streamlit Cloud).
    Se não encontrar, exibe campos na barra lateral para entrada manual.
    Retorna (url, key, api_key, fonte) onde fonte é 'secrets' ou 'sidebar'.
    """
    try:
        # st.secrets lê de .streamlit/secrets.toml (deploy) ou variáveis
        # de ambiente configuradas no Streamlit Cloud
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        api = st.secrets["GOOGLE_API_KEY"]
        return url, key, api, "secrets"
    except (KeyError, FileNotFoundError):
        pass  # Secrets não disponíveis — usa barra lateral

    # Fallback: sidebar para demonstração/desenvolvimento local
    with st.sidebar:
        st.header("🔑 Configurações de Acesso")
        st.caption(
            "Em produção (Streamlit Cloud), as chaves são configuradas em "
            "`secrets.toml`. Para demonstração, insira-as abaixo:"
        )
        url = st.text_input(
            "URL do Supabase",
            placeholder="https://xxx.supabase.co",
            type="password"
        )
        key = st.text_input(
            "Chave Service Role (Supabase)",
            placeholder="eyJ...",
            type="password"
        )
        api = st.text_input(
            "Chave Google API (Gemini)",
            placeholder="AIza...",
            type="password"
        )
    return url, key, api, "sidebar"


SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY, fonte = obter_credenciais()

# Interrompe a execução com orientação clara se alguma chave estiver faltando
if not (SUPABASE_URL and SUPABASE_KEY and GOOGLE_API_KEY):
    if fonte == "sidebar":
        st.warning("👈 Preencha todas as credenciais na barra lateral para iniciar o chat.")
    else:
        st.error(
            "❌ Credenciais incompletas no `secrets.toml`. "
            "Verifique as chaves `SUPABASE_URL`, `SUPABASE_KEY` e `GOOGLE_API_KEY`."
        )
    st.stop()


# ── Conexões com cache ────────────────────────────────────────────────────
# @st.cache_resource: inicializa os clientes UMA única vez por sessão de
# servidor. Sem isso, o Streamlit reconectaria a cada interação do usuário.
# As credenciais são passadas como parâmetros para invalidar o cache
# automaticamente caso as chaves mudem.

@st.cache_resource
def inicializar_clientes(url: str, key: str, api_key: str):
    """Inicializa e retorna os clientes Supabase e Google Gemini."""
    cliente_supabase = create_client(url, key)
    cliente_gemini   = genai.Client(api_key=api_key)
    return cliente_supabase, cliente_gemini

try:
    supabase, ai_client = inicializar_clientes(SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY)
except Exception as e:
    st.error(f"❌ Falha ao conectar aos serviços: {e}")
    st.info("Verifique se as credenciais estão corretas e tente recarregar a página.")
    st.stop()


# ── Histórico do chat ─────────────────────────────────────────────────────
# st.session_state persiste variáveis entre reruns do Streamlit
# durante a mesma sessão de navegador do usuário.

if "messages" not in st.session_state:
    st.session_state.messages = []

# Renderiza todas as mensagens anteriores da conversa
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── Fluxo RAG principal ───────────────────────────────────────────────────
# Ativado quando o usuário digita e envia uma pergunta no campo de chat.

if pergunta := st.chat_input("Ex: Como funciona o Split Payment no IBS?"):

    # Registra e exibe a mensagem do usuário
    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Buscando artigos relevantes no regulamento..."):
            try:

                # ── PASSO A: EMBEDDING DA PERGUNTA ───────────────────────
                # Transforma a pergunta em um vetor de 3072 dimensões.
                # Esse vetor será comparado matematicamente com os vetores
                # dos artigos armazenados no banco.
                resposta_emb = ai_client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=pergunta,
                    config={"output_dimensionality": 3072}
                )
                vetor_pergunta = resposta_emb.embeddings[0].values

                # ── PASSO B: BUSCA SEMÂNTICA NO SUPABASE ─────────────────
                # Envia o vetor ao banco via RPC (Remote Procedure Call).
                # A função 'buscar_artigos_ibs' calcula a distância do
                # cosseno e retorna os artigos mais próximos.
                resultado_busca = supabase.rpc(
                    "buscar_artigos_ibs",
                    {
                        "query_embedding": vetor_pergunta,
                        "match_threshold": 0.3,   # Similaridade mínima de 30%
                        "match_count":     4       # Top 4 artigos mais relevantes
                    }
                ).execute()

                artigos = resultado_busca.data

                # ── PASSO C: NENHUM ARTIGO RELEVANTE ENCONTRADO ──────────
                if not artigos:
                    resposta = (
                        "Não encontrei artigos no regulamento com relevância "
                        "suficiente para responder a esta pergunta. "
                        "Tente reformular ou pergunte sobre outro aspecto do IBS/CBS."
                    )
                    st.markdown(resposta)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": resposta}
                    )

                else:
                    # ── PASSO D: MONTAGEM DO CONTEXTO ────────────────────
                    # Reúne o conteúdo dos artigos recuperados em um bloco
                    # de texto que será entregue à IA como base da resposta.
                    contexto_juridico = ""
                    referencias       = []

                    for art in artigos:
                        livro    = art["metadata"].get("livro",    "")
                        titulo   = art["metadata"].get("titulo",   "")
                        capitulo = art["metadata"].get("capitulo", "")
                        sim      = art.get("similaridade", 0)

                        # Monta o cabeçalho com a localização hierárquica
                        partes   = [p for p in [livro, titulo, capitulo] if p]
                        cabecalho = " | ".join(partes) if partes else "Sem hierarquia"

                        contexto_juridico += (
                            f"\n[{art['id']} — {cabecalho}] "
                            f"(similaridade: {sim:.0%})\n"
                            f"{art['page_content']}\n"
                        )
                        referencias.append(art["id"].replace("_", " "))

                    # ── PASSO E: CONSTRUÇÃO DO PROMPT ─────────────────────
                    # O prompt instrui o modelo Gemini a agir como especialista
                    # tributário e a basear sua resposta EXCLUSIVAMENTE nos
                    # artigos fornecidos no contexto — prevenindo alucinações.
                    prompt_final = f"""Você é um contador e advogado especialista \
na Reforma Tributária brasileira (IBS/CBS), com profundo conhecimento da \
Resolução CGIBS Nº 6, de 30 de abril de 2026.

Responda à pergunta do usuário seguindo OBRIGATORIAMENTE estas regras:
1. Baseie-se EXCLUSIVAMENTE nos trechos do regulamento fornecidos abaixo.
2. Cite explicitamente o número do Artigo de onde retirou cada informação.
3. Se a resposta não estiver nos trechos, diga: "O regulamento não especifica isso nos artigos consultados."
4. Não use conhecimento externo ao contexto fornecido. Não invente informações.
5. Use linguagem clara, didática e tecnicamente precisa.

PERGUNTA DO USUÁRIO:
{pergunta}

TRECHOS OFICIAIS DO REGULAMENTO (sua única base de resposta):
{contexto_juridico}"""

                    # ── PASSO F: GERAÇÃO DA RESPOSTA ──────────────────────
                    resposta_llm = ai_client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=prompt_final
                    )

                    # Monta a resposta final com rodapé de referências
                    rodape = (
                        f"\n\n---\n"
                        f"📚 *Artigos consultados: {', '.join(referencias)}*"
                    )
                    resposta_completa = resposta_llm.text + rodape

                    # Exibe e registra no histórico da conversa
                    st.markdown(resposta_completa)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": resposta_completa}
                    )

            except Exception as e:
                st.error(f"❌ Erro no processamento: {str(e)}")
                st.info(
                    "Verifique se as credenciais estão corretas e se o banco "
                    "foi configurado conforme o Notebook 2."
                )
