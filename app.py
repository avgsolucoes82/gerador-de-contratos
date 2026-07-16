import streamlit as st
import requests
from docxtpl import DocxTemplate
import io
from datetime import datetime

st.set_page_config(page_title="Gerador de Contratos - Ball Park Go", layout="wide")
st.title("Gerador de Contratos - BALL PARK GO")

# --- SEÇÃO 1: DADOS DO CLIENTE ---
st.markdown("### 1. Dados do Cliente")
col_cnpj, col_vazio = st.columns([1, 2])
with col_cnpj:
    cnpj_digitado = st.text_input("Digite o CNPJ do Comprador (apenas números):")

col_email, col_tel = st.columns(2)
with col_email:
    email_cliente = st.text_input("E-mail do Comprador:")
with col_tel:
    telefone_cliente = st.text_input("Telefone/WhatsApp (Ex: (62) 8106-4636):")

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

# Medidas do brinquedo
col_comp, col_larg, col_alt, col_pav = st.columns(4)
with col_comp:
    medida_comp = st.text_input("Comprimento (Ex: 6,60m):")
with col_larg:
    medida_larg = st.text_input("Largura (Ex: 3,50m):")
with col_alt:
    medida_alt = st.text_input("Altura Final (Ex: 3m):")
with col_pav:
    medida_pav = st.number_input("Nº de Pavimentos:", min_value=1, value=3, step=1)

# Lista de atrativos disponíveis para seleção
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

# Cria caixinhas de quantidade apenas para os itens que foram selecionados
quantidades_itens = {}
if itens_selecionados:
    st.write("Informe a quantidade de cada atrativo selecionado:")
    cols_qtd = st.columns(4) # Cria 4 colunas para organizar as caixinhas
    for i, item in enumerate(itens_selecionados):
        col_atual = cols_qtd[i % 4]
        with col_atual:
            # Pede a quantidade, por padrão é 1
            qtd = st.number_input(f"Qtd: {item.title()}", min_value=1, value=1, key=f"qtd_{item}")
            quantidades_itens[item] = qtd


# --- SEÇÃO 4: GERAÇÃO DO CONTRATO ---
st.markdown("---")
if st.button("Buscar CNPJ e Gerar Contrato", type="primary"):
    if cnpj_digitado:
        # Consulta a BrasilAPI
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_digitado}"
        resposta = requests.get(url)
        
        if resposta.status_code == 200:
            dados_empresa = resposta.json()
            
            # Formata a string de endereço (Logradouro, numero, complemento, bairro)
            logradouro_completo = f"{dados_empresa.get('logradouro', '')}, {dados_empresa.get('numero', '')}"
            if dados_empresa.get('complemento'):
                logradouro_completo += f", {dados_empresa.get('complemento')}"
            logradouro_completo += f" - Bairro {dados_empresa.get('bairro', '')}"

            # ==========================================
            # A MÁGICA DA DESCRIÇÃO DO PRODUTO ACONTECE AQUI
            # ==========================================
            texto_descricao = f"Um complexo de Playground infantil “BRINQUEDÃO” contendo as seguintes medidas e especificações: {medida_comp} de comprimento; {medida_larg} de largura, {medida_alt} de altura final, {medida_pav} pavimentos"
            
            if quantidades_itens:
                texto_descricao += " com atrativos e obstáculos instalados em pontos aleatórios sendo: "
                # Cria uma lista de textos: "1 socão", "2 bananinhas", etc.
                lista_textos_itens = [f"{qtd} {nome}" for nome, qtd in quantidades_itens.items()]
                
                # Junta tudo com vírgulas e coloca um ponto final
                texto_descricao += ", ".join(lista_textos_itens) + "."
            else:
                texto_descricao += "." # Ponto final se não tiver atrativos
            # ==========================================

            # Carrega o modelo do Word
            doc = DocxTemplate("modelo.docx")
            
            # Preenche as Tags
            contexto = {
                "CNPJ": dados_empresa.get("cnpj", ""),
                "NOME_EMPRESARIAL": dados_empresa.get("razao_social", ""),
                "NOME_FANTASIA": dados_empresa.get("nome_fantasia", "") or dados_empresa.get("razao_social", ""),
                "LOGRADOURO": logradouro_completo,
                "CEP": dados_empresa.get("cep", ""),
                "MUNICIPIO": dados_empresa.get("municipio", ""),
                "UF": dados_empresa.get("uf", ""),
                "EMAIL": email_cliente,
                "TELEFONE": telefone_cliente,
                
                # Valores
                "VALOR_TOTAL": valor_total,
                "VALOR_ENTRADA": valor_entrada,
                "VALOR_SEGUNDA_PARCELA": valor_segunda,
                
                # A tag com a super descrição automática
                "DESCRICAO_PRODUTO": texto_descricao,
                
                # Data atual formatada (Ex: 29 de janeiro de 2026)
                "DATA_CONTRATO": datetime.now().strftime("%d/%m/%Y")
            }
            
            doc.render(contexto)
            
            arquivo_memoria = io.BytesIO()
            doc.save(arquivo_memoria)
            arquivo_memoria.seek(0)
            
            st.success("Contrato gerado com sucesso!")
            
            st.download_button(
                label="📥 Baixar Contrato Preenchido",
                data=arquivo_memoria,
                file_name=f"Contrato_BallParkGo_{cnpj_digitado}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.error("CNPJ não encontrado ou inválido.")
    else:
        st.warning("Por favor, digite o CNPJ do comprador.")