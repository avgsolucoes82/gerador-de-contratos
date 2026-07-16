import streamlit as st
import requests
from docxtpl import DocxTemplate
import io
import os
import subprocess
import tempfile
from datetime import datetime

st.set_page_config(page_title="Gerador de Contratos - Ball Park", layout="wide")
st.title("Gerador de Contratos - BALL PARK")

# ==========================================
# INICIALIZAÇÃO DA MEMÓRIA
# ==========================================
if "razao_social" not in st.session_state:
    st.session_state.update({
        "razao_social": "", "nome_fantasia": "", "logradouro": "",
        "cep": "", "municipio": "", "uf": "", "email": "", "telefone": ""
    })

def buscar_dados_cnpj():
    cnpj = st.session_state.cnpj_input.replace(".", "").replace("/", "").replace("-", "")
    
    if cnpj:
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
        resposta = requests.get(url)
        
        if resposta.status_code == 200:
            dados = resposta.json()
            st.session_state.razao_social = dados.get("razao_social", "")
            st.session_state.nome_fantasia = dados.get("nome_fantasia", "") or dados.get("razao_social", "")
            
            log_comp = f"{dados.get('logradouro', '')}, {dados.get('numero', '')}"
            if dados.get('complemento'):
                log_comp += f", {dados.get('complemento')}"
            log_comp += f" - Bairro {dados.get('bairro', '')}"
            
            st.session_state.logradouro = log_comp
            st.session_state.cep = dados.get("cep", "")
            st.session_state.municipio = dados.get("municipio", "")
            st.session_state.uf = dados.get("uf", "")
            st.session_state.email = dados.get("email", "")
            st.session_state.telefone = dados.get("ddd_telefone_1", "")
        else:
            st.error("CNPJ não encontrado ou inválido.")
    else:
        st.warning("Por favor, digite um CNPJ antes de buscar.")

# --- SEÇÃO 1: DADOS DO CLIENTE ---
st.markdown("### 1. Dados do Cliente")
col_cnpj, col_btn, col_vazio = st.columns([2, 1, 3])
with col_cnpj:
    st.text_input("Digite o CNPJ do Comprador (apenas números):", key="cnpj_input")
with col_btn:
    st.write("") 
    st.write("")
    st.button("🔍 Buscar CNPJ", on_click=buscar_dados_cnpj)

col_rz, col_fant = st.columns(2)
with col_rz:
    st.text_input("Razão Social:", key="razao_social")
with col_fant:
    st.text_input("Nome Fantasia:", key="nome_fantasia")

col_log, col_cep = st.columns([3, 1])
with col_log:
    st.text_input("Logradouro Completo:", key="logradouro")
with col_cep:
    st.text_input("CEP:", key="cep")

col_mun, col_uf, col_email, col_tel = st.columns(4)
with col_mun:
    st.text_input("Município:", key="municipio")
with col_uf:
    st.text_input("UF:", key="uf")
with col_email:
    st.text_input("E-mail:", key="email")
with col_tel:
    st.text_input("Telefone/WhatsApp:", key="telefone")

# --- SEÇÃO 2: DADOS FINANCEIROS ---
st.markdown("### 2. Dados Financeiros")
col_total, col_entrada, col_parcela = st.columns(3)
with col_total:
    valor_total = st.text_input("Valor Total (Ex: 13.200,00):")
with col_entrada:
    valor_entrada = st.text_input("Valor da Entrada (Ex: 6.250,00):")
with col_parcela:
    valor_segunda = st.text_input("Valor da 2ª Parcela (Ex: 6.250,00):")

# --- SEÇÃO 3: COMPOSIÇÃO DO BRINQUEDO ---
st.markdown("### 3. Especificações e Composição do Brinquedo")
col_comp, col_larg, col_alt, col_pav = st.columns(4)
with col_comp:
    medida_comp = st.text_input("Comprimento (Ex: 6,60m):")
with col_larg:
    medida_larg = st.text_input("Largura (Ex: 3,50m):")
with col_alt:
    medida_alt = st.text_input("Altura Final (Ex: 3m):")
with col_pav:
    medida_pav = st.number_input("Nº de Pavimentos:", min_value=1, value=3, step=1)

lista_atrativos = [
    "escorregador tubular caindo na piscina de bolinhas",
    "piscina de bolinhas em tela",
    "socão",
    "bananinhas",
    "ponte de fitas",
    "labirinto de fitas",
    "bolinhas coloridas",
    "saco de pancada",
    "túnel de fitas"
]

itens_selecionados = st.multiselect("Selecione os atrativos e obstáculos que compõem o projeto:", lista_atrativos)

quantidades_itens = {}
if itens_selecionados:
    st.write("Informe a quantidade de cada atrativo selecionado:")
    cols_qtd = st.columns(4)
    for i, item in enumerate(itens_selecionados):
        col_atual = cols_qtd[i % 4]
        with col_atual:
            qtd = st.number_input(f"Qtd: {item.title()}", min_value=1, value=1, key=f"qtd_{item}")
            quantidades_itens[item] = qtd

# --- SEÇÃO 4: GERAÇÃO DO CONTRATO ---
st.markdown("---")
st.markdown("### 4. Geração do Contrato")

# O usuário escolhe se quer em Word ou PDF
formato_saida = st.radio("Escolha o formato do arquivo:", ["Word (.docx)", "PDF (.pdf)"], horizontal=True)

if st.button("📝 Gerar Contrato", type="primary"):
    
    if st.session_state.razao_social == "":
        st.error("Por favor, busque um CNPJ ou preencha os dados do cliente antes de gerar o contrato.")
    else:
        # Monta a descrição
        texto_descricao = f"Um complexo de Playground infantil “BRINQUEDÃO” contendo as seguintes medidas e especificações: {medida_comp} de comprimento; {medida_larg} de largura, {medida_alt} de altura final, {medida_pav} pavimentos"
        
        if quantidades_itens:
            texto_descricao += " com atrativos e obstáculos instalados em pontos aleatórios sendo: "
            lista_textos_itens = [f"{qtd} {nome}" for nome, qtd in quantidades_itens.items()]
            texto_descricao += ", ".join(lista_textos_itens) + "."
        else:
            texto_descricao += "."

        # Carrega e preenche o Word
        doc = DocxTemplate("modelo.docx")
        contexto = {
            "CNPJ": st.session_state.cnpj_input,
            "NOME_EMPRESARIAL": st.session_state.razao_social,
            "NOME_FANTASIA": st.session_state.nome_fantasia,
            "LOGRADOURO": st.session_state.logradouro,
            "CEP": st.session_state.cep,
            "MUNICIPIO": st.session_state.municipio,
            "UF": st.session_state.uf,
            "EMAIL": st.session_state.email,
            "TELEFONE": st.session_state.telefone,
            "VALOR_TOTAL": valor_total,
            "VALOR_ENTRADA": valor_entrada,
            "VALOR_SEGUNDA_PARCELA": valor_segunda,
            "DESCRICAO_PRODUTO": texto_descricao,
            "DATA_CONTRATO": datetime.now().strftime("%d/%m/%Y")
        }
        
        doc.render(contexto)
        
        # Lógica de Exportação baseada na escolha do usuário
        if formato_saida == "Word (.docx)":
            arquivo_memoria = io.BytesIO()
            doc.save(arquivo_memoria)
            arquivo_memoria.seek(0)
            
            st.success("Contrato gerado com sucesso em Word!")
            st.download_button(
                label="📥 Baixar Contrato (Word)",
                data=arquivo_memoria,
                file_name=f"Contrato_BallParkGo_{st.session_state.cnpj_input}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
        elif formato_saida == "PDF (.pdf)":
            # Mostra um aviso de carregamento pois o PDF demora uns 2 segundos a mais
            with st.spinner("Convertendo o arquivo para PDF. Aguarde alguns segundos..."):
                
                # Salva o arquivo temporário no servidor
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_docx:
                    doc.save(tmp_docx.name)
                    caminho_docx = tmp_docx.name
                
                caminho_pdf = caminho_docx.replace(".docx", ".pdf")
                
                # Roda o comando invisível do LibreOffice
                comando = [
                    "libreoffice", "--headless", "--convert-to", "pdf",
                    "--outdir", os.path.dirname(caminho_pdf), caminho_docx
                ]
                
                try:
                    subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                    
                    # Lê o PDF gerado
                    with open(caminho_pdf, "rb") as arquivo_pdf:
                        dados_pdf = arquivo_pdf.read()
                        
                    st.success("Contrato gerado com sucesso em PDF!")
                    st.download_button(
                        label="📥 Baixar Contrato (PDF)",
                        data=dados_pdf,
                        file_name=f"Contrato_BallParkGo_{st.session_state.cnpj_input}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error("Ocorreu um erro ao converter para PDF. Verifique se o arquivo packages.txt está configurado.")
                finally:
                    # Limpa os arquivos temporários para não lotar o servidor do Streamlit
                    if os.path.exists(caminho_docx): os.remove(caminho_docx)
                    if os.path.exists(caminho_pdf): os.remove(caminho_pdf)