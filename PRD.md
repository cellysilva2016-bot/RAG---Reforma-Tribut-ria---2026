# Product Requirements Document (PRD)
## Produto: Assistente RAG — Especialista em Reforma Tributária (IBS/CBS)
## Distribuição permitida, construído por Rômulo Negi Camargo para fins acadêmicos.
---

### 1. Visão Geral do Produto

Um assistente virtual conversacional baseado em Inteligência Artificial, desenhado para atuar como especialista jurídico-tributário focado na Reforma Tributária do Consumo brasileiro — especificamente na **Resolução CGIBS Nº 6, de 30 de abril de 2026**, que regulamenta o Imposto sobre Bens e Serviços (IBS).

---

### 2. A Problemática

A legislação tributária brasileira é densa e estruturada em hierarquias complexas (Livros, Títulos, Capítulos, Seções). Documentos em PDF dificultam a busca por contexto: a pesquisa tradicional por palavras-chave perde a amarração jurídica do artigo com suas exceções e regimes específicos.

Profissionais da área — contadores, advogados, consultores — demandam respostas rápidas, precisas e livres de alucinações para tomarem decisões seguras sobre apuração, alíquotas e inovações como o *Split Payment* e o *Cashback* (Devolução Personalizada).

---

### 3. A Essência — Proposta de Valor

O produto resolve essa dor utilizando a técnica de **Retrieval-Augmented Generation (RAG)**. A essência do sistema não é "ensinar" a lei genérica à IA, mas sim:

1. **Fatiar** a legislação artigo por artigo, preservando o "endereço" de cada um (metadados hierárquicos)
2. **Vetorizar** matematicamente cada artigo usando embeddings de alta dimensão
3. **Forçar** a IA a formular respostas baseadas exclusivamente nos trechos oficiais recuperados do banco de dados, citando as fontes de origem

---

### 4. Público-Alvo

| Perfil | Necessidade Principal |
|---|---|
| Contadores e Auditores Fiscais | Verificação rápida de regras de apuração e alíquotas |
| Advogados Tributaristas | Localização de dispositivos legais e suas exceções |
| Gestores Financeiros | Entendimento operacional das obrigações do IBS/CBS |
| Desenvolvedores de ERP/Fiscal | Referência técnica para implementação de regras tributárias |
| Estudantes e Professores | Ferramenta didática para exploração da Reforma Tributária |

---

### 5. Casos de Uso Principais

- Consulta de regras gerais de **Fato Gerador** e **Base de Cálculo** do IBS
- Verificação de **Regimes Específicos e Diferenciados** (Serviços Financeiros, Saúde, Educação, Seguros)
- Entendimento operacional do **Split Payment** e da **Devolução Personalizada (Cashback)**
- Localização de artigos por tema sem precisar navegar pelo PDF
- Comparação de tratamentos tributários entre operações distintas

---

### 6. Premissas e Restrições

- O sistema responde **exclusivamente** com base nos artigos da Resolução CGIBS Nº 6/2026
- Não substitui consulta jurídica ou parecer contábil profissional
- A qualidade das respostas depende da precisão da extração do PDF e da qualidade dos embeddings
- O plano gratuito do Supabase é suficiente para uso acadêmico e demonstrações (617 artigos)

---

### 7. Critérios de Sucesso

- Respostas fundamentadas em artigos reais, com citação explícita da fonte
- Busca semântica funcional: perguntas em linguagem natural encontram artigos relevantes
- Interface conversacional com histórico de chat
- Deploy funcional no Streamlit Community Cloud
