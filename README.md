# Assistente_de_Investimento
 
# Assessor de Investimentos - Coletor e Analisador de Dados

## Descrição
Este projeto tem como objetivo coletar e analisar dados de investimentos de ações e fundos imobiliários (FIIs) a partir do site **Fundamentus** e da API do **Yahoo Finance**. Ele filtra e aplica fórmulas de análise fundamentalista para identificar oportunidades de investimentos. Os dados são integrados ao **Power BI** para visualização interativa e insights estratégicos.

## Funcionalidades
- **Coleta de Dados:** 
  - Obtém informações de ações e FIIs do site Fundamentus.
  - Obtém histórico de dividendos e informações adicionais via Yahoo Finance.
  
- **Análise e Filtros:** 
  - Aplica critérios de seleção com base em indicadores financeiros (ROE, P/L, Dividend Yield, entre outros).
  - Implementa estratégias como a **Fórmula Mágica de ROE** e **análise de FIIs por vacância e rendimentos**.

- **Exportação e Armazenamento:**
  - Salva os dados filtrados em arquivos CSV.
  - **Em breve:** Migrar o armazenamento de CSV para **MySQL** para melhorar a escalabilidade e atualização automática.

- **Visualização de Dados:**
  - Integração com **Power BI** para análise interativa e relatórios visuais.

## Tecnologias Utilizadas
- **Linguagem:** Python
- **Bibliotecas:**
  - `pandas` - Manipulação de dados
  - `requests` - Coleta de dados via HTTP
  - `BeautifulSoup` - Web scraping
  - `yfinance` - Consulta de dados financeiros
  - `sqlalchemy` e `pymysql` - Conexão e manipulação de banco de dados
  - **Power BI** - Visualização de dados e relatórios interativos

## Instalação e Uso
### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as credenciais do banco de dados
Edite o arquivo `db_config.py` (ou altere as variáveis no script principal) com suas credenciais do MySQL.

### 4. Execute o script
```bash
python main.py
```

## Estrutura do Projeto
```
/
|-- main.py                # Script principal para coleta e análise
|-- db_config.py           # Configuração do banco de dados
|-- requirements.txt       # Lista de dependências
|-- README.md              # Este arquivo
```

## Melhorias Futuras
- **Migrar de CSV para MySQL** para facilitar a escalabilidade e atualização dos dados.
- **Automatizar a coleta diária** para garantir que os dados estejam sempre atualizados.
- **Adicionar novos indicadores** e aprimorar os filtros de seleção.
- **Criar um dashboard avançado no Power BI** com mais insights sobre os investimentos.

## Autor
- **Seu Nome** - [LinkedIn](https://www.linkedin.com/in/seu-perfil)

## Licença
Este projeto está licenciado sob a Licença MIT - veja o arquivo `LICENSE` para mais detalhes.

