import streamlit as st
import requests
import json
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Configuração
API_BASE_URL = "http://localhost:8000"  # URL do FastAPI backend
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Credenciais do cartório (em produção, use um banco de dados seguro)
CARTORIO_USERS = {
    "admin": "admin123",
    "cartorio": "cert2024"
}

# Inicializa cliente OpenAI
client = None

def init_openai():
    """Inicializa o cliente OpenAI"""
    global client
    if client is None and OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
    return client


def check_login(username: str, password: str) -> bool:
    """Verifica as credenciais do usuário"""
    return CARTORIO_USERS.get(username) == password


def logout():
    """Realiza o logout do usuário"""
    st.session_state['logged_in'] = False
    st.session_state['username'] = None

def translate_to_citizen_language(technical_data: dict, context: str = "verificação") -> str:
    """Usa OpenAI para traduzir dados técnicos em linguagem cidadã"""
    openai_client = init_openai()
    if not openai_client:
        return None
    
    prompt = f"""Você é um assistente que ajuda cidadãos a entenderem informações de certidões 
armazenadas em blockchain. Traduza as informações técnicas abaixo em uma linguagem simples, 
clara e amigável que qualquer pessoa possa entender.

Contexto: {context}

Dados técnicos:
{json.dumps(technical_data, indent=2, ensure_ascii=False)}

Instruções:
- Use linguagem simples e direta
- Evite termos técnicos como "hash", "blockchain", "ledger"
- Explique o que cada informação significa para o cidadão
- Se houver verificação de integridade (hashMatch), explique se o documento é autêntico
- IMPORTANTE: Os timestamps estão em UTC. Converta para horário de Brasília (UTC-3) ao mencionar datas/horários
- Formate de forma amigável com emojis quando apropriado
- Seja conciso mas completo"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em explicar documentos oficiais para cidadãos comuns. Sempre converta horários UTC para horário de Brasília (UTC-3)."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Erro ao usar OpenAI: {e}")
        return None


def translate_history_to_citizen_language(history_data: list) -> str:
    """Traduz o histórico de alterações para linguagem cidadã"""
    openai_client = init_openai()
    if not openai_client:
        return None
    
    prompt = f"""Você é um assistente que ajuda cidadãos a entenderem o histórico de suas certidões 
armazenadas em blockchain. Traduza o histórico abaixo em uma linguagem simples.

Histórico técnico:
{json.dumps(history_data, indent=2, ensure_ascii=False)}

Instruções:
- Explique cada alteração de forma cronológica
- Use linguagem simples como "Em [data], sua certidão foi [ação]"
- IMPORTANTE: Os timestamps estão em UTC. Converta para horário de Brasília (UTC-3) ao mencionar datas/horários. Por exemplo, se o timestamp mostrar "2024-01-15T03:30:00Z", exiba como "15/01/2024 às 00:30 (horário de Brasília)"
- Explique que cada registro é permanente e não pode ser alterado
- Use emojis para tornar mais amigável
- Se não houver alterações, explique que o documento permanece original"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Você é um assistente especializado em explicar documentos oficiais para cidadãos comuns. Sempre converta horários UTC para horário de Brasília (UTC-3)."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Erro ao usar OpenAI: {e}")
        return None


def verify_certificate(cert_id: str):
    """Chama a API para verificar uma certidão"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/certidao/verify",
            json={"cert_id": cert_id},
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def get_history(cert_id: str):
    """Chama a API para obter o histórico de uma certidão"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/certidao/history",
            json={"cert_id": cert_id},
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def register_certificate(cert_data: dict):
    """Chama a API para registrar uma nova certidão"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/certidao/register",
            json=cert_data,
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def update_certificate(cert_id: str, field_name: str, new_value: str):
    """Chama a API para atualizar uma certidão"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/certidao/update",
            json={
                "cert_id": cert_id,
                "field_name": field_name,
                "new_value": new_value
            },
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ============== Interface Streamlit ==============

st.set_page_config(
    page_title="Verificação de Certidões",
    page_icon="📜",
    layout="wide"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        background-color: transparent;
        border: 2px solid #10B981;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: transparent;
        border: 2px solid #F59E0B;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: transparent;
        border: 2px solid #3B82F6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📜 Verificação de Certidões em Blockchain</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar para informações
with st.sidebar:
    st.header("ℹ️ Sobre")
    st.markdown("""
    Este sistema permite que você verifique a autenticidade 
    de certidões registradas em blockchain.
    
    **Suas certidões são:**
    - 🔒 Seguras e imutáveis
    - ✅ Verificáveis a qualquer momento
    - 📋 Com histórico completo
    """)
    
    st.markdown("---")
    
    # Status da conexão com OpenAI
    if OPENAI_API_KEY:
        st.success("✅ Tradução automática ativada")
    else:
        st.warning("⚠️ Tradução automática desativada")
    
    st.markdown("---")
    
    # Navegação
    st.header("🧭 Navegação")
    pagina = st.radio(
        "Selecione a página:",
        ["👤 Área do Cidadão", "🏛️ Área do Cartório"],
        label_visibility="collapsed"
    )

# ============== Área do Cartório ==============
if pagina == "🏛️ Área do Cartório":
    st.markdown('<h1 class="main-header">🏛️ Área do Cartório</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Verifica se está logado
    if not st.session_state.get('logged_in', False):
        # Tela de login
        st.subheader("🔐 Acesso Restrito")
        st.markdown("Esta área é exclusiva para funcionários do cartório.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.markdown("### Faça seu login")
                username = st.text_input("Usuário", placeholder="Digite seu usuário")
                password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                
                submit = st.form_submit_button("🔓 Entrar", use_container_width=True)
                
                if submit:
                    if check_login(username, password):
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.rerun()
                    else:
                        st.error("❌ Usuário ou senha incorretos!")
    
    else:
        # Área logada do cartório
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ Logado como: **{st.session_state.get('username')}**")
        with col2:
            if st.button("🚪 Sair", use_container_width=True):
                logout()
                st.rerun()
        
        st.markdown("---")
        
        # Tabs de funcionalidades do cartório
        tab_registrar, tab_editar, tab_consultar = st.tabs([
            "📝 Registrar Certidão", 
            "✏️ Editar Certidão", 
            "🔍 Consultar Certidão"
        ])
        
        # Tab: Registrar Certidão
        with tab_registrar:
            st.header("📝 Registrar Nova Certidão")
            
            with st.form("register_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    cert_id = st.text_input("Código da Certidão *", placeholder="Ex: CERT001")
                    nome = st.text_input("Nome Completo *", placeholder="Nome da pessoa")
                    data_nascimento = st.date_input("Data de Nascimento *")
                    hora_nascimento = st.time_input("Hora de Nascimento *")
                    hospital = st.text_input("Local de Nascimento *", placeholder="Hospital/Maternidade")
                
                with col2:
                    pai = st.text_input("Nome do Pai *", placeholder="Nome completo do pai")
                    mae = st.text_input("Nome da Mãe *", placeholder="Nome completo da mãe")
                    cartorio = st.text_input("Cartório *", placeholder="Nome do cartório")
                    cartorio_reg = st.text_input("Registro do Cartório *", placeholder="Número do registro")
                
                st.markdown("**Metadados (opcional)**")
                col1, col2 = st.columns(2)
                with col1:
                    doc_type = st.selectbox("Tipo de Documento", ["birth", "marriage", "death"])
                with col2:
                    notes = st.text_input("Observações", placeholder="Notas adicionais")
                
                submit_register = st.form_submit_button("📝 Registrar Certidão", use_container_width=True)
                
                if submit_register:
                    if not all([cert_id, nome, hospital, pai, mae, cartorio, cartorio_reg]):
                        st.error("❌ Preencha todos os campos obrigatórios!")
                    else:
                        cert_data = {
                            "cert_id": cert_id,
                            "nome": nome,
                            "data": str(data_nascimento),
                            "hora": str(hora_nascimento),
                            "hospital": hospital,
                            "pai": pai,
                            "mae": mae,
                            "cartorio": cartorio,
                            "cartorio_reg": cartorio_reg,
                            "metadata": {
                                "docType": doc_type,
                                "notes": notes
                            }
                        }
                        
                        with st.spinner("Registrando na blockchain..."):
                            result = register_certificate(cert_data)
                        
                        if "error" in result:
                            st.error(f"❌ Erro ao registrar: {result['error']}")
                        elif result.get("status") == "success":
                            st.success(f"✅ Certidão **{cert_id}** registrada com sucesso na blockchain!")
                        else:
                            st.error("❌ Erro ao registrar certidão.")
        
        # Tab: Editar Certidão
        with tab_editar:
            st.header("✏️ Editar Certidão Existente")
            
            st.warning("⚠️ **Atenção:** Todas as alterações são registradas permanentemente na blockchain.")
            
            with st.form("edit_form"):
                cert_id_edit = st.text_input("Código da Certidão *", placeholder="Ex: CERT001", key="edit_cert_id")
                
                field_options = {
                    "Nome": "name",
                    "Data de Nascimento": "dateofbirth",
                    "Hora de Nascimento": "timeofbirth",
                    "Local de Nascimento": "placeofbirth",
                    "Nome do Pai": "fathername",
                    "Nome da Mãe": "mothername",
                    "Proprietário": "owner",
                    "Cartório": "source"
                }
                
                field_label = st.selectbox("Campo a ser alterado *", list(field_options.keys()))
                new_value = st.text_input("Novo valor *", placeholder="Digite o novo valor")
                
                submit_edit = st.form_submit_button("✏️ Atualizar Certidão", use_container_width=True)
                
                if submit_edit:
                    if not all([cert_id_edit, new_value]):
                        st.error("❌ Preencha todos os campos!")
                    else:
                        field_name = field_options[field_label]
                        
                        with st.spinner("Atualizando na blockchain..."):
                            result = update_certificate(cert_id_edit, field_name, new_value)
                        
                        if "error" in result:
                            st.error(f"❌ Erro ao atualizar: {result['error']}")
                        elif result.get("status") == "success":
                            st.success(f"✅ Campo **{field_label}** da certidão **{cert_id_edit}** atualizado com sucesso!")
                        else:
                            st.error("❌ Erro ao atualizar certidão.")
        
        # Tab: Consultar Certidão
        with tab_consultar:
            st.header("🔍 Consultar Certidão")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                cert_id_search = st.text_input("Código da Certidão", placeholder="Ex: CERT001", key="search_cert_id")
            with col2:
                st.write("")
                st.write("")
                search_button = st.button("🔍 Buscar", use_container_width=True)
            
            if search_button and cert_id_search:
                with st.spinner("Consultando blockchain..."):
                    result = verify_certificate(cert_id_search)
                    history_result = get_history(cert_id_search)
                
                if "error" in result:
                    st.error(f"❌ Erro ao consultar: {result['error']}")
                elif result.get("status") == "success":
                    data = result.get("data", {})
                    
                    if isinstance(data, dict) and data.get("found"):
                        record = data.get("record", {})
                        hash_match = data.get("hashMatch", False)
                        
                        # Status
                        if hash_match:
                            st.success("✅ Certidão encontrada e íntegra!")
                        else:
                            st.warning("⚠️ Certidão encontrada, mas há inconsistências no hash.")
                        
                        # Dados
                        st.subheader("📋 Dados da Certidão")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown(f"**ID:** {record.get('id', 'N/A')}")
                            st.markdown(f"**Nome:** {record.get('name', 'N/A')}")
                            st.markdown(f"**Data de Nascimento:** {record.get('dateOfBirth', 'N/A')}")
                            st.markdown(f"**Hora de Nascimento:** {record.get('timeOfBirth', 'N/A')}")
                            st.markdown(f"**Local de Nascimento:** {record.get('placeOfBirth', 'N/A')}")
                        
                        with col2:
                            st.markdown(f"**Nome do Pai:** {record.get('fatherName', 'N/A')}")
                            st.markdown(f"**Nome da Mãe:** {record.get('motherName', 'N/A')}")
                            st.markdown(f"**Cartório:** {record.get('source', 'N/A')}")
                            st.markdown(f"**Proprietário:** {record.get('owner', 'N/A')}")
                            st.markdown(f"**Registrado em:** {record.get('timestamp', 'N/A')}")
                        
                        # Hash técnico
                        with st.expander("🔧 Dados Técnicos"):
                            st.markdown(f"**Hash:** `{record.get('hash', 'N/A')}`")
                            st.json(data)
                        
                        # Histórico
                        st.subheader("📜 Histórico de Alterações")
                        if history_result.get("status") == "success":
                            history = history_result.get("history", [])
                            if history:
                                for i, item in enumerate(history):
                                    timestamp = item.get("timestamp", "Data desconhecida")
                                    is_delete = item.get("isDelete", False)
                                    
                                    if is_delete:
                                        st.markdown(f"🗑️ **{timestamp}** - Registro removido")
                                    else:
                                        st.markdown(f"📝 **{timestamp}** - Registro criado/atualizado")
                                    
                                    with st.expander(f"Detalhes da transação {i+1}"):
                                        st.markdown(f"**TX ID:** `{item.get('txId', 'N/A')}`")
                                        if item.get("value"):
                                            st.json(item["value"])
                            else:
                                st.info("Nenhum histórico encontrado.")
                    else:
                        st.warning(f"⚠️ Certidão **{cert_id_search}** não encontrada.")

# ============== Área do Cidadão ==============
else:
    tab1, tab2 = st.tabs(["🔍 Verificar Certidão", "📜 Ver Histórico"])

    with tab1:
        st.header("Verificar Autenticidade da Certidão")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cert_id = st.text_input(
                "Digite o código da sua certidão:",
                placeholder="Ex: CERT001",
                help="O código único da sua certidão que deseja verificar"
            )
        
        with col2:
            st.write("")  # Espaçamento
            st.write("")
            verify_button = st.button("🔍 Verificar", type="primary", use_container_width=True)
        
        if verify_button and cert_id:
            with st.spinner("Consultando blockchain..."):
                result = verify_certificate(cert_id)
            
            if "error" in result:
                st.error(f"❌ Erro ao consultar: {result['error']}")
            elif result.get("status") == "success":
                data = result.get("data", {})
                
                # Verifica se encontrou
                if isinstance(data, dict) and data.get("found"):
                    record = data.get("record", {})
                    hash_match = data.get("hashMatch", False)
                    
                    # Status de verificação
                    if hash_match:
                        st.markdown("""
                        <div class="success-box">
                            <h3>✅ Certidão Autêntica!</h3>
                            <p>Este documento foi verificado e está íntegro na blockchain.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="warning-box">
                            <h3>⚠️ Atenção!</h3>
                            <p>A verificação de integridade encontrou inconsistências. Consulte o cartório.</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Dados da certidão
                    st.subheader("📋 Dados da Certidão")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown(f"**Nome:** {record.get('name', 'N/A')}")
                        st.markdown(f"**Data de Nascimento:** {record.get('dateOfBirth', 'N/A')}")
                        st.markdown(f"**Hora de Nascimento:** {record.get('timeOfBirth', 'N/A')}")
                        st.markdown(f"**Local de Nascimento:** {record.get('placeOfBirth', 'N/A')}")
                    
                    with col2:
                        st.markdown(f"**Nome do Pai:** {record.get('fatherName', 'N/A')}")
                        st.markdown(f"**Nome da Mãe:** {record.get('motherName', 'N/A')}")
                        st.markdown(f"**Cartório:** {record.get('source', 'N/A')}")
                        st.markdown(f"**Registrado em:** {record.get('timestamp', 'N/A')}")
                    
                    # Tradução para linguagem cidadã
                    st.markdown("---")
                    st.subheader("💬 Explicação em Linguagem Simples")
                    
                    if OPENAI_API_KEY:
                        with st.spinner("Gerando explicação..."):
                            citizen_explanation = translate_to_citizen_language(data)
                        
                        if citizen_explanation:
                            st.markdown(f"""
                            <div class="info-box">
                                {citizen_explanation}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("💡 A tradução automática está desativada. Configure a variável OPENAI_API_KEY no arquivo .env")
                    
                    # Dados técnicos (expandível)
                    with st.expander("🔧 Ver dados técnicos"):
                        st.json(data)
                else:
                    st.warning(f"⚠️ Certidão com código '{cert_id}' não encontrada.")
            else:
                st.error("❌ Erro na verificação. Tente novamente.")

    with tab2:
        st.header("Histórico de Alterações da Certidão")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            hist_cert_id = st.text_input(
                "Digite o código da certidão:",
                placeholder="Ex: CERT001",
                key="hist_cert_id",
                help="O código único da certidão para consultar o histórico"
            )
        
        with col2:
            st.write("")
            st.write("")
            history_button = st.button("📜 Ver Histórico", type="primary", use_container_width=True)
        
        if history_button and hist_cert_id:
            with st.spinner("Consultando histórico na blockchain..."):
                result = get_history(hist_cert_id)
            
            if "error" in result:
                st.error(f"❌ Erro ao consultar: {result['error']}")
            elif result.get("status") == "success":
                history = result.get("history", [])
                
                if history:
                    st.success(f"📋 Encontrados {len(history)} registro(s) no histórico")
                    
                    # Tradução para linguagem cidadã (primeiro, antes dos detalhes técnicos)
                    st.subheader("💬 Explicação do Histórico")
                    
                    if OPENAI_API_KEY:
                        with st.spinner("Gerando explicação..."):
                            citizen_explanation = translate_history_to_citizen_language(history)
                        
                        if citizen_explanation:
                            st.markdown(f"""
                            <div class="info-box">
                                {citizen_explanation}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("💡 A tradução automática está desativada. Configure a variável OPENAI_API_KEY no arquivo .env")
                    
                    st.markdown("---")
                    
                    # Timeline visual
                    st.subheader("📜 Detalhes Técnicos")
                    for i, item in enumerate(history):
                        with st.container():
                            timestamp = item.get("timestamp", "Data desconhecida")
                            tx_id = item.get("txId", "N/A")[:16] + "..."
                            is_delete = item.get("isDelete", False)
                            
                            if is_delete:
                                st.markdown(f"🗑️ **{timestamp}** - Registro removido")
                            else:
                                st.markdown(f"📝 **{timestamp}** - Registro atualizado")
                            
                            with st.expander(f"Ver detalhes da transação {i+1}"):
                                st.markdown(f"**ID da Transação:** `{item.get('txId', 'N/A')}`")
                                if item.get("value"):
                                    st.json(item["value"])
                else:
                    st.info(f"ℹ️ Nenhum histórico encontrado para a certidão '{hist_cert_id}'.")
            else:
                st.error("❌ Erro ao consultar histórico. Tente novamente.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6B7280; font-size: 0.875rem;">
    🔐 Sistema de Verificação de Certidões em Blockchain<br>
    Seus documentos protegidos com tecnologia de ponta
</div>
""", unsafe_allow_html=True)