# Estratégia DevSecOps e Auditoria de Segurança

## 1. Objetivo

O pipeline DevSecOps foi definido para inserir verificações de segurança ao longo do ciclo de desenvolvimento da aplicação, evitando que vulnerabilidades conhecidas ou de alta criticidade avancem para o ambiente de produção.

A estratégia foi definida considerando o histórico de vulnerabilidades identificado durante o Assessment, principalmente problemas relacionados a autorização, BOLA, validação de entradas, XSS, SQL Injection, autenticação, exposição de dados sensíveis e dependências vulneráveis.

---

## 2. Distribuição das ferramentas no SDLC

### 2.1 SAST — Static Application Security Testing

O SAST será executado durante o desenvolvimento e principalmente no Pull Request/CI, antes do merge para a branch principal.

O objetivo é analisar o código-fonte sem executar a aplicação e identificar problemas de segurança diretamente na implementação.

Exemplos de problemas que podem ser encontrados:

- SQL Injection;
- uso inseguro de informações sensíveis;
- problemas de autenticação;
- falhas de validação de entrada;
- configurações inseguras;
- padrões de código potencialmente vulneráveis.

A utilização do SAST nessa etapa permite encontrar problemas de forma antecipada e com menor custo de correção.

---

### 2.2 SCA — Software Composition Analysis

A análise de dependências será executada no Pull Request e no pipeline de CI.

O objetivo é verificar as bibliotecas utilizadas pela aplicação e identificar versões que possuam vulnerabilidades conhecidas.

Essa análise é importante porque a aplicação utiliza dependências como:

- FastAPI;
- SQLModel;
- Pydantic;
- PyJWT;
- pwdlib;
- httpx;
- pytest;
- pydantic-settings.

Uma vulnerabilidade presente em uma dependência pode comprometer a aplicação mesmo que o código desenvolvido internamente esteja correto.

---

### 2.3 DAST — Dynamic Application Security Testing

O DAST será executado depois que a aplicação for iniciada em um ambiente de teste.

Diferentemente do SAST, o DAST testa a aplicação em funcionamento, enviando requisições e observando suas respostas.

O objetivo é identificar vulnerabilidades que somente podem ser observadas durante a execução da aplicação.

Entre os vetores relevantes estão:

- autenticação;
- autorização;
- BOLA;
- exposição indevida de recursos;
- XSS;
- comportamento incorreto de endpoints;
- configurações inseguras.

O DAST será executado depois das verificações estáticas e de dependências, pois depende da aplicação estar disponível para receber requisições.

---

### 2.4 IAST — Interactive Application Security Testing

O IAST será utilizado durante a execução dos testes de integração e segurança em ambiente controlado.

A ferramenta acompanha a execução da aplicação enquanto os testes são realizados, permitindo observar o comportamento interno durante as requisições.

Essa abordagem é útil para complementar SAST e DAST, principalmente na identificação de vulnerabilidades relacionadas ao fluxo de dados, autenticação, autorização e acesso ao banco de dados.

---

## 3. Ordem definida para o pipeline

A ordem escolhida será:

1. Instalação das dependências;
2. SAST;
3. SCA;
4. Execução dos testes automatizados;
5. Inicialização da aplicação em ambiente de teste;
6. DAST;
7. IAST, quando disponível;
8. Security Gate;
9. Deploy somente se todas as condições obrigatórias forem atendidas.

Essa ordem prioriza verificações rápidas e antecipadas antes das análises que dependem da aplicação em execução.

---

## 4. Critério de bloqueio

O pipeline será configurado para bloquear o processo quando for identificada uma vulnerabilidade classificada como:

- Critical;
- High.

Vulnerabilidades classificadas como Medium ou Low serão registradas para acompanhamento, mas não bloquearão automaticamente o pipeline.

A escolha desse critério considera que a aplicação processa dados pessoais e informações relacionadas à saúde. Vulnerabilidades de alta gravidade podem permitir acesso indevido, alteração ou exposição de informações sensíveis.

---

## 5. Justificativa do Security Gate

O bloqueio para vulnerabilidades Critical e High reduz o risco de realizar um deploy contendo falhas capazes de comprometer diretamente:

- confidencialidade dos dados dos pacientes;
- integridade das consultas;
- autenticação dos usuários;
- autorização de acesso;
- dados pessoais;
- informações relacionadas à saúde.

Como a aplicação possui dados sensíveis, permitir o deploy de uma vulnerabilidade crítica ou alta sem correção representa um risco de negócio significativo.

Vulnerabilidades Medium e Low continuam sendo registradas para correção posterior, evitando que problemas de menor impacto impeçam desnecessariamente todo o ciclo de entrega.

---

## 6. Relação com o Threat Model

A estratégia de testes será baseada nos vetores de ataque identificados durante o Threat Model dos exercícios anteriores.

Os principais riscos considerados são:

- acesso não autorizado a recursos de outros usuários;
- BOLA;
- falhas de autenticação;
- falhas de autorização;
- abuso de escopos OAuth2;
- SQL Injection;
- XSS;
- manipulação de entradas;
- exposição de dados sensíveis;
- vulnerabilidades em dependências;
- abuso de endpoints de autenticação.

Esses riscos serão utilizados para definir os testes automatizados de segurança executados no pipeline.