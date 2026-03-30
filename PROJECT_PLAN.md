# PROJECT_PLAN.md

## 1. Visão Geral do Projeto

### Objetivo
Construir uma API orientada por busca de empresa, capaz de receber o **nome de uma empresa** como entrada, coletar avaliações e reclamações públicas em fontes relevantes — inicialmente **Reclame Aqui** e **Google Play Store** — e aplicar **classificação com IA** para identificar:

- **Sentimento** do comentário/reclamação
- **Tags de intenção** (motivo principal ou tema do comentário)

O sistema deve consolidar os dados em uma estrutura padronizada, permitindo consumo por uma interface web e por integrações futuras.

### Problema que o projeto resolve
Empresas e times de produto/atendimento normalmente precisam acompanhar reputação digital em múltiplos canais. Hoje esse trabalho costuma ser manual, demorado e inconsistente. A proposta desta API é centralizar a coleta, normalização e análise inteligente dos comentários para gerar:

- visão unificada da reputação da empresa;
- distribuição de sentimento por canal;
- principais dores, elogios e intenções dos usuários;
- base para dashboards, alertas e análises históricas.

### Escopo inicial (MVP)
O MVP deve contemplar:

1. Input por nome da empresa.
2. Busca/coleta de dados em:
   - Reclame Aqui
   - Play Store
3. Padronização dos registros coletados.
4. Classificação via IA com:
   - sentimento: positivo, neutro, negativo;
   - tags de intenção: conjunto definido pela área de negócios.
5. Exposição dos resultados por API.
6. Interface web para consulta e visualização básica.

### Resultados esperados
Ao informar uma empresa, o sistema deverá retornar algo como:

- empresa consultada;
- fontes pesquisadas;
- comentários/reclamações encontrados;
- classificação de sentimento por item;
- tags de intenção por item;
- agregados para dashboard:
  - volume por fonte;
  - volume por sentimento;
  - top intenções;
  - tendências simples por período.

---

## 2. Arquitetura Sugerida

### Visão arquitetural
Arquitetura modular, separando coleta, processamento com IA, persistência e exposição dos dados.

```text
[Frontend React]
      |
      v
[API Backend Python]
      |
      +--> [Serviço de Busca da Empresa]
      |
      +--> [Módulo de Coleta Reclame Aqui]
      |
      +--> [Módulo de Coleta Play Store]
      |
      +--> [Pipeline de Normalização]
      |
      +--> [Módulo de Classificação IA]
      |
      +--> [Banco de Dados]
      |
      +--> [Cache / Fila opcional]
```

### Componentes principais

#### 2.1 Frontend (React)
Responsável por:
- receber o nome da empresa;
- iniciar a consulta;
- exibir status do processamento;
- mostrar comentários classificados;
- renderizar dashboards e filtros.

#### 2.2 API Backend (Python)
Responsável por:
- receber a requisição do frontend;
- orquestrar a busca da empresa nas fontes;
- acionar scraping/coleta;
- normalizar os dados;
- chamar o serviço/modelo de IA para classificação;
- persistir e expor os resultados.

#### 2.3 Módulos de coleta
**Reclame Aqui**
- Localizar a empresa/plataforma correspondente.
- Extrair reclamações, título, texto, data, status, nota (se disponível), categoria e metadados.
- Lidar com paginação, limite de requisições, mudança de layout e possíveis bloqueios.

**Play Store**
- Localizar o app relacionado à empresa.
- Coletar reviews, nota, texto, versão, data e metadados relevantes.
- Definir estratégia para múltiplos apps da mesma empresa.

#### 2.4 Pipeline de normalização
Converter dados de múltiplas fontes para um schema único, por exemplo:

```json
{
  "company_name": "Empresa X",
  "source": "play_store",
  "source_item_id": "abc123",
  "title": "",
  "comment_text": "O app trava ao abrir",
  "rating": 1,
  "date": "2026-03-30",
  "status": null,
  "metadata": {
    "app_version": "2.3.1"
  }
}
```

#### 2.5 Módulo de classificação com IA
Responsável por analisar cada comentário/reclamação e retornar:

- sentimento;
- uma ou mais tags de intenção;
- opcionalmente, confiança da classificação;
- justificativa resumida para auditoria interna.

Exemplo de saída:

```json
{
  "sentiment": "negativo",
  "intent_tags": ["bug", "instabilidade", "experiencia_ruim"],
  "confidence": 0.91,
  "reason": "Usuário relata travamento e frustração com uso do app."
}
```

#### 2.6 Banco de dados
Sugestão: **PostgreSQL**.

Tabelas iniciais sugeridas:
- `companies`
- `search_requests`
- `sources`
- `raw_reviews`
- `normalized_reviews`
- `ai_classifications`
- `processing_logs`

#### 2.7 Cache e fila (opcional no MVP, recomendável na evolução)
Sugestões:
- **Redis** para cache de consultas recentes;
- **Celery/RQ** para processamento assíncrono de scraping e IA.

Isso ajuda quando a coleta demorar mais que o aceitável para uma requisição síncrona.

---

## 3. Fluxo Funcional do Sistema

### Fluxo principal
1. Usuário informa o nome da empresa no frontend.
2. Frontend chama a API backend.
3. Backend verifica se já existe resultado recente em cache/banco.
4. Se não existir, inicia pipeline:
   - localizar empresa nas fontes;
   - coletar dados do Reclame Aqui;
   - coletar dados da Play Store;
   - normalizar registros;
   - classificar comentários com IA;
   - salvar no banco.
5. Backend retorna resultados processados ou status da execução.
6. Frontend apresenta lista, filtros e dashboards.

### Estratégia recomendada de execução
Para boa experiência do usuário, recomenda-se trabalhar com **processamento assíncrono**:

- `POST /search` cria uma busca;
- retorna um `search_id` e status `processing`;
- frontend consulta `GET /search/{id}`;
- resultados aparecem assim que o pipeline concluir.

Essa abordagem é mais robusta do que tentar coletar e classificar tudo em uma única chamada síncrona.

---

## 4. Sugestão de Stack Tecnológica

### Backend
- **Python 3.11+**
- **FastAPI** para API REST
- **Pydantic** para schemas
- **SQLAlchemy** para ORM
- **PostgreSQL** para persistência
- **Redis** para cache/fila (opcional inicialmente)
- **Celery** ou **RQ** para jobs assíncronos
- Bibliotecas de scraping:
  - `httpx` / `requests`
  - `BeautifulSoup`
  - `Playwright` ou `Selenium` se houver necessidade de páginas dinâmicas
- Integração com IA:
  - API de LLM (OpenAI, Anthropic, Gemini etc.) ou modelo local/fine-tuned no futuro

### Frontend
- **React**
- **Vite** ou **Next.js**
- **TypeScript**
- **Tailwind CSS** ou biblioteca de UI (MUI/Ant Design)
- **Recharts** ou **Chart.js** para dashboards
- **React Query / TanStack Query** para consumo da API

### Infraestrutura
- Docker / Docker Compose para ambiente local
- Deploy inicial em VPS, Render, Railway, Fly.io ou AWS
- Monitoramento com logs estruturados e Sentry opcionalmente

---

## 5. Modelo de Dados Sugerido

### Entidade: Company
- id
- name
- aliases
- created_at

### Entidade: SearchRequest
- id
- company_name_input
- normalized_company_name
- status (`pending`, `processing`, `completed`, `failed`)
- requested_at
- completed_at

### Entidade: Review/Complaint
- id
- company_id
- source (`reclame_aqui`, `play_store`)
- source_item_id
- title
- comment_text
- rating
- complaint_status
- published_at
- author_name (se público e permitido)
- raw_payload

### Entidade: AIClassification
- id
- review_id
- sentiment
- intent_tags
- confidence
- model_name
- model_version
- classified_at
- explanation

---

## 6. API Endpoints Sugeridos

### Criar consulta
**POST** `/search`

Request:
```json
{
  "company_name": "Nubank"
}
```

Response:
```json
{
  "search_id": "uuid",
  "status": "processing"
}
```

### Consultar status/resultados
**GET** `/search/{search_id}`

Response:
```json
{
  "search_id": "uuid",
  "status": "completed",
  "company_name": "Nubank",
  "summary": {
    "total_items": 250,
    "by_source": {
      "reclame_aqui": 100,
      "play_store": 150
    },
    "by_sentiment": {
      "positivo": 80,
      "neutro": 40,
      "negativo": 130
    }
  },
  "items": []
}
```

### Listar comentários com filtro
**GET** `/reviews?search_id=...&source=play_store&sentiment=negativo`

### Dashboard agregado
**GET** `/dashboard/{search_id}`

Retorna:
- distribuição por sentimento;
- top tags de intenção;
- evolução temporal;
- distribuição por fonte.

---

## 7. Estratégia de Classificação com IA

### Objetivo da IA
Transformar texto livre em estrutura analítica útil para negócios.

### Saídas mínimas
- **Sentimento**:
  - positivo
  - neutro
  - negativo

- **Intenção**:
  - conjunto fechado de tags inicialmente definido pela área de negócios.

### Exemplo de taxonomia inicial de intenção
Essa lista deve ser refinada pela área de negócios, mas um ponto de partida razoável seria:

- bug/erro técnico
- lentidão/performance
- login/acesso
- cobrança/pagamento
- atendimento/suporte
- cancelamento
- usabilidade
- funcionalidade ausente
- elogio ao produto
- elogio ao atendimento
- reclamação geral
- segurança/confiabilidade

### Abordagem recomendada
#### Fase 1 — Prompt-based classification
Usar LLM via API para classificar cada comentário com instruções rígidas e retorno em JSON.

Vantagens:
- implementação rápida;
- fácil ajuste de taxonomia;
- boa qualidade para MVP.

#### Fase 2 — Avaliação e refinamento
- montar conjunto de validação manual;
- medir concordância entre IA e negócio;
- revisar prompts, exemplos e regras.

#### Fase 3 — Escala
Se o volume crescer muito:
- batch processing;
- embeddings para clusterização auxiliar;
- eventual modelo especializado/fine-tuned.

---

## 8. Riscos e Pontos de Atenção

### 8.1 Scraping e conformidade
- Reclame Aqui pode alterar layout ou impor restrições.
- É preciso validar limites técnicos e jurídicos do scraping.
- Onde houver API oficial ou formas mais estáveis, elas devem ser priorizadas.

### 8.2 Resolução de identidade da empresa
- O nome digitado pode mapear para múltiplas empresas/apps.
- Será necessário criar lógica de matching e possivelmente etapa de confirmação quando houver ambiguidade.

### 8.3 Qualidade da classificação
- Sentimento e intenção podem ser ambíguos.
- Necessário processo de validação com negócio para evitar distorções nos dashboards.

### 8.4 Custo de IA
- Classificar grandes volumes via API pode ficar caro.
- Recomendado cachear resultados por texto/hash e usar processamento incremental.

### 8.5 Latência
- Scraping + IA pode levar tempo.
- Processamento assíncrono é a opção mais segura para UX e escalabilidade.

---

## 9. Roadmap por Fases

### Fase 1 — Descoberta e definição
- Definir fontes e viabilidade técnica.
- Definir taxonomia inicial de intenção.
- Definir critérios de sentimento.
- Desenhar schema de dados.
- Validar fluxo do input por nome da empresa.

### Fase 2 — MVP técnico
- Implementar backend base com FastAPI.
- Implementar scraper do Reclame Aqui.
- Implementar coletor da Play Store.
- Normalizar dados em schema único.
- Integrar classificação com IA.
- Persistir dados no PostgreSQL.
- Criar endpoints principais.

### Fase 3 — Interface web
- Criar tela de busca por empresa.
- Criar listagem de comentários.
- Criar filtros por fonte/sentimento/tag.
- Criar dashboard inicial.

### Fase 4 — Validação e refinamento
- Revisar qualidade das classificações.
- Ajustar prompts/tags.
- Melhorar matching da empresa.
- Ajustar performance e observabilidade.

### Fase 5 — Evolução
- Histórico de buscas.
- Comparação entre empresas.
- Alertas automáticos.
- Exportação CSV/Excel.
- Mais fontes além de Reclame Aqui e Play Store.

---

## 10. Divisão de Tarefas por Agente

## 10.1 Dev Backend (Python)
Responsável pela espinha dorsal do sistema: coleta, processamento e API.

### Entregas principais
1. **Arquitetura do backend**
   - Estruturar projeto em módulos: API, services, scrapers, AI, repository, jobs.
   - Configurar FastAPI, banco e autenticação básica se necessário.

2. **Input e busca da empresa**
   - Criar endpoint que recebe `company_name`.
   - Implementar normalização de nome.
   - Criar lógica de matching da empresa nas fontes.

3. **Scraping / coleta de dados**
   - Implementar módulo de coleta do Reclame Aqui.
   - Implementar módulo de coleta da Play Store.
   - Lidar com paginação, erros, retries e logging.
   - Salvar payload bruto para auditoria.

4. **Normalização dos dados**
   - Padronizar estruturas entre fontes.
   - Validar schemas.
   - Remover duplicidades quando aplicável.

5. **Integração com IA**
   - Criar cliente para serviço de IA.
   - Definir prompt/contrato JSON de classificação.
   - Implementar classificação de sentimento e intenção.
   - Tratar falhas, timeouts e reprocessamento.

6. **Persistência e consulta**
   - Modelar banco.
   - Criar migrations.
   - Persistir buscas, reviews e classificações.
   - Criar endpoints de consulta e dashboard.

7. **Processamento assíncrono**
   - Implementar fila/jobs para scraping e classificação.
   - Atualizar status da busca.

8. **Qualidade e operação**
   - Testes unitários e integrados.
   - Logs estruturados.
   - Documentação Swagger/OpenAPI.

### Checklist técnico sugerido
- [ ] Criar estrutura base do projeto FastAPI
- [ ] Definir models e migrations
- [ ] Implementar `POST /search`
- [ ] Implementar `GET /search/{id}`
- [ ] Implementar scraper Reclame Aqui
- [ ] Implementar coletor Play Store
- [ ] Criar normalizador de dados
- [ ] Integrar serviço de IA
- [ ] Implementar agregações para dashboard
- [ ] Adicionar testes e logs

---

## 10.2 Dev Frontend (React)
Responsável pela experiência de uso e visualização analítica.

### Entregas principais
1. **Tela de busca**
   - Campo para nome da empresa.
   - Disparo da consulta.
   - Exibição de loading/status.

2. **Tela de resultados**
   - Lista de comentários/reclamações.
   - Exibição de fonte, data, nota, sentimento e tags.
   - Paginação ou carregamento incremental.

3. **Dashboard**
   - Cards com métricas gerais.
   - Gráficos de sentimento.
   - Gráficos de top intenções.
   - Filtros por fonte, período e sentimento.

4. **Experiência de acompanhamento do processamento**
   - Estado `processing`, `completed`, `failed`.
   - Polling do status da busca.
   - Mensagens de erro amigáveis.

5. **Organização e qualidade**
   - Componentização.
   - Tipagem com TypeScript.
   - Integração com API usando React Query.
   - Testes básicos de interface.

### Checklist técnico sugerido
- [ ] Criar projeto React com TypeScript
- [ ] Montar layout principal
- [ ] Implementar formulário de busca
- [ ] Integrar `POST /search`
- [ ] Integrar polling de status
- [ ] Criar lista de reviews
- [ ] Criar filtros
- [ ] Criar gráficos do dashboard
- [ ] Tratar estados vazios e erros

---

## 10.3 Negócios
Responsável por transformar a análise em algo útil e confiável para tomada de decisão.

### Entregas principais
1. **Definição de tags de intenção**
   - Criar taxonomia inicial.
   - Definir descrição objetiva para cada tag.
   - Evitar sobreposição excessiva entre categorias.

2. **Critérios de sentimento**
   - Definir o que caracteriza positivo, neutro e negativo.
   - Criar exemplos reais e limítrofes.
   - Especificar regras para casos ambíguos.

3. **Validação dos resultados**
   - Separar amostra de comentários.
   - Classificar manualmente uma base de referência.
   - Comparar resultado humano x IA.
   - Aprovar ajustes de prompt/tags.

4. **Definição dos indicadores do dashboard**
   - Quais métricas importam mais para o negócio.
   - Como interpretar top intenções.
   - Quais filtros devem existir na versão inicial.

5. **Governança da análise**
   - Revisar periodicamente a taxonomia.
   - Validar se novas categorias precisam surgir.
   - Acompanhar precisão percebida pelos stakeholders.

### Checklist de negócio sugerido
- [ ] Definir lista oficial de tags de intenção
- [ ] Documentar critérios de sentimento
- [ ] Criar base de validação manual
- [ ] Revisar amostras classificadas pela IA
- [ ] Aprovar versão inicial do dashboard
- [ ] Definir métricas de sucesso do MVP

---

## 11. Critérios de Sucesso do MVP

O MVP será considerado bem-sucedido se conseguir:

- receber o nome da empresa e retornar dados utilizáveis;
- coletar dados das duas fontes principais com estabilidade mínima;
- classificar sentimento e intenção com qualidade aceitável para análise exploratória;
- apresentar dashboard claro para leitura executiva;
- permitir revisão manual e refinamento da taxonomia.

### KPIs sugeridos
- tempo médio de processamento por busca;
- quantidade média de comentários coletados por fonte;
- taxa de falha por fonte;
- concordância entre IA e validação humana;
- taxa de reutilização via cache;
- satisfação dos usuários internos com os dashboards.

---

## 12. Recomendação Final

A melhor estratégia é começar com um **MVP enxuto e modular**:
- backend em Python com FastAPI;
- processamento assíncrono;
- scraping/coleta por conectores separados;
- classificação via LLM com taxonomia definida pelo negócio;
- frontend React para busca e visualização;
- validação forte da área de negócios desde o início.

O principal ponto crítico não é só a tecnologia, e sim a **qualidade da taxonomia de intenção** e a **estabilidade da coleta**. Se essas duas frentes forem bem tratadas, o projeto rapidamente vira uma base sólida para monitoramento de reputação e inteligência de produto/atendimento.
