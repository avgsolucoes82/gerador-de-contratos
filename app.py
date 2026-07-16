import streamlit as st
import requests
from docxtpl import DocxTemplate
import io

st.title("Gerador de Contratos Automatizado")

# 1. Campo para digitar o CNPJ
cnpj_digitado = st.text_input("Digite o CNPJ (somente números):")

if st.button("Buscar e Gerar Contrato"):
    if cnpj_digitado:
        # 2. Chama a API Pública
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_digitado}"
        resposta = requests.get(url)
        
        if resposta.status_code == 200:
            dados_empresa = resposta.json()
            
            # 3. Carrega o Word e faz o "De-Para" das Tags
            doc = DocxTemplate("modelo.docx")
            
            # Aqui dizemos que a tag {{ razao_social }} recebe o dado da API
            contexto = {
                "razao_social": dados_empresa.get("razao_social"),
                "nome_fantasia": dados_empresa.get("nome_fantasia"),
                "cnpj": dados_empresa.get("cnpj"),                                
                "logradouro": dados_empresa.get("logradouro"),
                "numero": dados_empresa.get("numero"),
                "complemento": dados_empresa.get("complemento"),
                "bairro": dados_empresa.get("bairro"),
                "municipio": dados_empresa.get("municipio")
            }
            
            doc.render(contexto) # Preenche o documento!
            
            # 4. Prepara o arquivo para o usuário baixar
            arquivo_memoria = io.BytesIO()
            doc.save(arquivo_memoria)
            arquivo_memoria.seek(0)
            
            st.success("Contrato gerado com sucesso!")
            
            # Este botão do Streamlit força o download que pisca no navegador
            st.download_button(
                label="📥 Baixar e Abrir Contrato",
                data=arquivo_memoria,
                file_name=f"Contrato_{cnpj_digitado}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        else:
            st.error("CNPJ não encontrado ou inválido.")