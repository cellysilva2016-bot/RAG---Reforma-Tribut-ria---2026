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
def obter_credenciais():
    """
    Tenta ler credenciais do st.secrets (produção no Streamlit Cloud).
    Se não encontrar, exibe campos na barra lateral para entrada manual.
    Retorna (url, key, api_key, fonte) onde fonte é 'secrets' ou 'sidebar'.
    """
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        api = st.secrets["GOOGLE_API_KEY"]
        return url, key, api, "secrets"
    except (KeyError, FileNotFoundError):
        pass

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
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ── Fluxo RAG principal ───────────────────────────────────────────────────
if pergunta := st.chat_input("Ex: Como funciona o Split Payment no IBS?"):

    st.session_state.messages.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Buscando artigos relevantes no regulamento..."):
            try:
                # ── PASSO A: EMBEDDING DA PERGUNTA ───────────────────────
                resposta_emb = ai_client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=pergunta,
                    config={"output_dimensionality": 3072}
                )
                vetor_pergunta = resposta_emb.embeddings[0].values

                # ── PASSO B: BUSCA SEMÂNTICA NO SUPABASE ─────────────────
                resultado_busca = supabase.rpc(
                    "buscar_artigos_ibs",
                    {
                        "query_embedding": vetor_pergunta,
                        "match_threshold": 0.3,
                        "match_count":     4
                    }
                ).execute()

                artigos = resultado_busca.data

                # ── PASSO C: NENHUM ARTIGO RELEVANTE ENCONTRADO ──────────
                if not artigos:
                    resposta = (
                        "Não encontrei artigos no regulamento com relevância "
                        "suficiente para responder a esta pergunta. "
                        "Tente reformular ou pergunte sobre outro aspect do IBS/CBS."
                    )
                    st.markdown(resposta)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": resposta}
                    )

                else:
                    # ── PASSO D: MONTAGEM DO CONTEXTO ────────────────────
                    contexto_juridico = ""
                    referencias       = []

                    for art in artigos:
                        livro    = art["metadata"].get("livro",    "")
                        titulo   = art["metadata"].get("titulo",   "")
                        capitulo = art["metadata"].get("capitulo", "")
                        sim      = art.get("similaridade", 0)

                        partes   = [p for p in [livro, titulo, capitulo] if p]
                        cabecalho = " | ".join(partes) if partes else "Sem hierarquia"
                        
                        contexto_juridico += f"\n\n[{cabecalho}]\n{art['content']}"
                        referencias.append(f"• {cabecalho} (Similaridade: {sim:.2%})")

                    # ── PASSO E: ENVIO AO GEMINI 3.5 FLASH ───────────────
                    system_instruction = (
                        "Você é um advogado tributarista especialista na Reforma Tributária. "
                        "Responda à pergunta do usuário utilizando unicamente o contexto fornecido. "
                        "Seja preciso e cite os trechos relevantes."
                    )
                    
                    prompt = f"Contexto:\n{contexto_juridico}\n\nPergunta: {pergunta}"
                    
                    # Chamada corrigida para a versão estável atualizada
                    resposta_ai = ai_client.models.generate_content(
                        model='gemini-3.5-flash',
                        contents=prompt,
                        config={"system_instruction": system_instruction}
                    )
                    
                    resposta_final = resposta_ai.text
                    
                    # Exibe o resultado e as referências
                    st.markdown(resposta_final)
                    with st.expander("📚 Fontes consultadas no banco de dados"):
                        for ref in referencias:
                            st.write(ref)
                            
                    st.session_state.messages.append(
                        {"role": "assistant", "content": resposta_final}
                    )
                    
            except Exception as e:
                st.error(f"Erro ao processar a requisição: {e}")
