import streamlit as st
import requests
from docxtpl import DocxTemplate
import io
import os
import subprocess
import tempfile
from datetime import datetime
import base64
import streamlit.components.v1 as components
from num2words import num2words

st.set_page_config(page_title="Gerador de Contratos - Ball Park", layout="wide")
st.title("Gerador de Contratos - BALL PARK")

# ==========================================
# TRUQUE DE CSS
# Deixa em negrito os textos digitados em caixas de texto e número
# ==========================================
st.markdown("""
    <style>
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stTextArea"] textarea {
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# INICIALIZAÇÃO DA MEMÓRIA
# ==========================================
if "razao_social" not in st.session_state:
    st.session_state.update({
        "razao_social": "", "nome_fantasia": "", "logradouro": "",
        "cep": "", "municipio": "", "uf": "", "email": "", "telefone": ""
    })

# ==========================================
# FUNÇÕES DE FORMATAÇÃO E CÁLCULO
# ==========================================
def formatar_cnpj(cnpj):
    if not cnpj: return ""
    cnpj_limpo = ''.join(filter(str.isdigit, str(cnpj)))
    if len(cnpj_limpo) == 14:
        return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:]}"
    return cnpj

def formatar_cep(cep):
    if not cep: return ""
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    if len(cep_limpo) == 8:
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    return cep

def formatar_telefone(telefone):
    if not telefone: return ""
    tel_limpo = ''.join(filter(str.isdigit, str(telefone)))
    if len(tel_limpo) == 11: # Celular (com nono dígito)
        return f"({tel_limpo[:2]}) {tel_limpo[2:7]}-{tel_limpo[7:]}"
    elif len(tel_limpo) == 10: # Fixo
        return f"({tel_limpo[:2]}) {tel_limpo[2:6]}-{tel_limpo[6:]}"
    return telefone

def formatar_moeda(valor_string):
    if not valor_string:
        return ""
    try:
        valor_limpo = str(valor_string).replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_float = float(valor_limpo)
        valor_formatado = f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return valor_formatado
    except ValueError:
        return valor_string 

def valor_por_extenso(valor_string):
    if not valor_string:
        return ""
    try:
        valor_limpo = str(valor_string).replace("R$", "").replace(".", "").replace(",", ".").strip()
        valor_float = float(valor_limpo)
        extenso = num2words(valor_float, lang='pt_BR', to='currency')
        return extenso.capitalize()
    except ValueError:
        return "Valor inválido"

def data_por_extenso():
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    hoje = datetime.now()
    return f"{hoje.day:02d} de {meses[hoje.month - 1]} de {hoje.year}"

# ==========================================
# FUNÇÃO DE BUSCA NA API
# ==========================================
def buscar_dados_cnpj():
    cnpj = st.session_state.cnpj_input.replace(".", "").replace("/", "").replace("-", "")
    
    if cnpj:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        resposta = requests.get(url)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            st.session_state.razao_social = dados.get("razao_social") or ""
            st.session_state.nome_fantasia = dados.get("nome_fantasia") or dados.get("razao_social") or ""
            
            log_comp = f"{dados.get('logradouro') or ''}, {dados.get('numero') or ''}"
            if dados.get('complemento'):
                log_comp += f", {dados.get('complemento')}"
            log_comp += f" - Bairro {dados.get('bairro') or ''}"
            
            st.session_state.logradouro = log_comp
            
            st.session_state.cep = formatar_cep(dados.get("cep") or "")
            st.session_state.telefone = formatar_telefone(dados.get("ddd_telefone_1") or "")
            
            st.session_state.municipio = dados.get("municipio") or ""
            st.session_state.uf = dados.get("uf") or ""
            st.session_state.email = dados.get("email") or ""
            
            st.session_state.cnpj_input = formatar_cnpj(cnpj)
        else:
            st.error("CNPJ não encontrado ou inválido.")
    else:
        st.warning("Por favor, digite um CNPJ antes de buscar.")
        
# --- SEÇÃO 1: DADOS DO CLIENTE ---
st.markdown("### 1. Dados do Cliente")
col_cnpj, col_btn, col_vazio = st.columns([2, 1, 3])
with col_cnpj:
    st.text_input("**Digite o CNPJ do Comprador (apenas números):**", key="cnpj_input")
with col_btn:
    st.write("") 
    st.write("")
    st.button("🔍 Buscar CNPJ", on_click=buscar_dados_cnpj)

col_rz, col_fant = st.columns(2)
with col_rz:
    st.text_input("**Razão Social:**", key="razao_social")
with col_fant:
    st.text_input("**Nome Fantasia:**", key="nome_fantasia")

col_log, col_cep = st.columns([3, 1])
with col_log:
    st.text_input("**Logradouro Completo:**", key="logradouro")
with col_cep:
    st.text_input("**CEP:**", key="cep")

col_mun, col_uf, col_email, col_tel = st.columns(4)
with col_mun:
    st.text_input("**Município:**", key="municipio")
with col_uf:
    st.text_input("**UF:**", key="uf")
with col_email:
    st.text_input("**E-mail:**", key="email")
with col_tel:
    st.text_input("**Telefone/WhatsApp:**", key="telefone")

# --- SEÇÃO 2: CONDIÇÕES COMERCIAIS ---
st.markdown("### 2. Condições Comerciais")

# Primeira linha: Preço e Prazo
col_valor, col_prazo = st.columns(2)
with col_valor:
    valor_total = st.text_input("**Preço Total:**") 
with col_prazo:
    prazo_entrega = st.number_input("**Prazo de entrega (em dias úteis):**", min_value=1, value=30, step=1)

st.markdown("#### Configuração de Pagamento")
col_tipo, col_meio = st.columns(2)
with col_tipo:
    tipo_pagamento = st.radio("**Modalidade:**", ["À vista", "Parcelado"], horizontal=True)
with col_meio:
    meio_pagamento = st.selectbox("**Meio de Pagamento:**", ["PIX", "Boleto", "Cartão de Crédito"])

# Lógica condicional dinâmica para o texto
texto_gerado_pagamento = ""

if tipo_pagamento == "À vista":
    if valor_total:
        texto_gerado_pagamento = f"Pagamento à vista no valor de {formatar_moeda(valor_total)}, a ser realizado via {meio_pagamento}."
    else:
        texto_gerado_pagamento = f"Pagamento à vista no valor total do contrato, a ser realizado via {meio_pagamento}."
else:
    col_ent, col_qtd, col_parc = st.columns(3)
    with col_ent:
        valor_entrada = st.text_input("**Valor da Entrada:**", key="entrada")
    with col_qtd:
        qtd_parcelas = st.number_input("**Nº de Parcelas:**", min_value=1, value=1, step=1)
    with col_parc:
        valor_parcela = st.text_input("**Valor da Parcela:**", key="parcela")
    
    entrada_fmt = formatar_moeda(valor_entrada) if valor_entrada else "[VALOR DA ENTRADA]"
    parcela_fmt = formatar_moeda(valor_parcela) if valor_parcela else "[VALOR DA PARCELA]"
    
    texto_gerado_pagamento = f"Pagamento parcelado, sendo uma entrada no valor de {entrada_fmt} e o saldo remanescente dividido em {qtd_parcelas} parcela(s) de {parcela_fmt}, a serem pagos via {meio_pagamento}."

st.markdown("<br>", unsafe_allow_html=True)
st.info("💡 O texto abaixo foi gerado automaticamente, mas você pode editá-lo livremente antes de gerar o contrato.")

# Caixa de texto final, preenchida pelo texto gerado, mas editável pelo usuário
condicoes_pagamento = st.text_area("**Texto Final das Condições de Pagamento:**", value=texto_gerado_pagamento, height=100)

# --- SEÇÃO 3: COMPOSIÇÃO DO BRINQUEDO ---
st.markdown("### 3. Especificações e Composição do Brinquedo")

st.info("ℹ️ Medidas em metros")

col_comp, col_larg, col_alt, col_pav = st.columns(4)
with col_comp:
    medida_comp = st.text_input("**Comprimento:**")
with col_larg:
    medida_larg = st.text_input("**Largura na parte do Escorregador:**")
with col_alt:
    medida_alt = st.text_input("**Altura Final:**")
with col_pav:
    medida_pav = st.number_input("**Nº de Pavimentos:**", min_value=1, value=3, step=1)

lista_atrativos = [
    "Escorregador reto",
    "Escorregador duplo",
    "Escorregador tubular",
    "Piscina de bolinhas",
    "Pula pula",
    "Sapateira",
    "Cavalinho",
    "Mesinha com cadeiras em MDF",
    "Cenários",
    "Cercado com portão",
    "Socão",
    "Bananinhas",
    "Ponte de fitas",
    "Meia lua",
    "Labirinto de fitas",
    "Bolinhas coloridas"
]

itens_selecionados = st.multiselect("**Selecione os atrativos e obstáculos que compõem o projeto:**", lista_atrativos)

quantidades_itens = {}
if itens_selecionados:
    st.write("**Informe a quantidade de cada atrativo selecionado:**")
    cols_qtd = st.columns(4)
    for i, item in enumerate(itens_selecionados):
        col_atual = cols_qtd[i % 4]
        with col_atual:
            qtd = st.number_input(f"**Qtd: {item}**", min_value=1, value=1, key=f"qtd_{item}")
            quantidades_itens[item] = qtd

# --- SEÇÃO 4: GERAÇÃO DO CONTRATO ---
st.markdown("---")
st.markdown("### 4. Geração do Contrato")

formato_saida = st.radio("**Escolha o formato do arquivo:**", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)

def download_automatico(dados_arquivo, nome_arquivo, mime_type):
    b64 = base64.b64encode(dados_arquivo).decode()
    js_codigo = f"""
        <html>
            <body>
                <a id="link_invisivel" href="data:{mime_type};base64,{b64}" download="{nome_arquivo}"></a>
                <script>
                    document.getElementById('link_invisivel').click();
                </script>
            </body>
        </html>
    """
    components.html(js_codigo, height=0)

if st.button("📝 Gerar e Baixar Contrato", type="primary"):
    
    if st.session_state.razao_social == "":
        st.error("Por favor, busque um CNPJ ou preencha os dados do cliente antes de gerar o contrato.")
    else:
        texto_descricao = f"Um complexo de Playground infantil “BRINQUEDÃO” contendo as seguintes medidas e especificações: {medida_comp}m de comprimento; {medida_larg}m de largura na parte do escorregador, {medida_alt}m de altura final, {medida_pav} pavimentos"
        
        if quantidades_itens:
            texto_descricao += " com atrativos e obstáculos instalados em pontos aleatórios sendo: "
            lista_textos_itens = [f"{qtd} {nome}" for nome, qtd in quantidades_itens.items()]
            texto_descricao += ", ".join(lista_textos_itens) + "."
        else:
            texto_descricao += "."

        doc = DocxTemplate("contrato.docx")
        
        contexto = {
            "CNPJ": formatar_cnpj(st.session_state.cnpj_input) or "",
            "NOME_EMPRESARIAL": st.session_state.razao_social or "",
            "NOME_FANTASIA": st.session_state.nome_fantasia or "",
            "LOGRADOURO": st.session_state.logradouro or "",
            "CEP": formatar_cep(st.session_state.cep) or "",
            "MUNICIPIO": st.session_state.municipio or "",
            "UF": st.session_state.uf or "",
            "EMAIL": st.session_state.email or "",
            "TELEFONE": formatar_telefone(st.session_state.telefone) or "",
            "VALOR_TOTAL": formatar_moeda(valor_total) or "",
            "VALOR_EXTENSO": valor_por_extenso(valor_total) or "",
            "CONDICOES_PAGAMENTO": condicoes_pagamento or "",
            "PRAZO_ENTREGA": str(prazo_entrega),
            "DESCRICAO_PRODUTO": texto_descricao or "",
            "DATA_CONTRATO": data_por_extenso() 
        }
        
        doc.render(contexto)
        
        cnpj_arquivo = ''.join(filter(str.isdigit, str(st.session_state.cnpj_input)))
        
        if formato_saida == "Word (.docx)":
            arquivo_memoria = io.BytesIO()
            doc.save(arquivo_memoria)
            
            nome_arq = f"Contrato_BallPark_{cnpj_arquivo}.docx"
            mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            
            st.success("Contrato gerado com sucesso! O download começará automaticamente.")
            download_automatico(arquivo_memoria.getvalue(), nome_arq, mime)
            
        elif formato_saida == "PDF (.pdf)":
            with st.spinner("Convertendo o arquivo para PDF. O download começará em instantes..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
                    doc.save(tmp_docx.name)
                    caminho_docx = tmp_docx.name
                
                caminho_pdf = caminho_docx.replace(".docx", ".pdf")
                
                comando = [
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", os.path.dirname(caminho_pdf), caminho_docx
                ]
                
                try:
                    subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    
                    with open(caminho_pdf, "rb") as arquivo_pdf:
                        dados_pdf = arquivo_pdf.read()
                        
                    nome_arq = f"Contrato_BallPark_{cnpj_arquivo}.pdf"
                    mime = "application/pdf"
                    
                    st.success("PDF gerado com sucesso! O download começará automaticamente.")
                    download_automatico(dados_pdf, nome_arq, mime)
                    
                except Exception as e:
                    st.error("Ocorreu um erro ao converter para PDF. Verifique se o arquivo packages.txt está configurado.")
                finally:
                    if os.path.exists(caminho_docx): os.remove(caminho_docx)
                    if os.path.exists(caminho_pdf): os.remove(caminho_pdf)
