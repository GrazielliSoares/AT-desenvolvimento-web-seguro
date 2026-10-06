# Relatório Final — Exercício 13
## Auditoria, Rastreabilidade e Segurança da API

## 1. Objetivo

Este relatório apresenta a auditoria final de segurança da API REST de agendamento de consultas médicas, desenvolvida com FastAPI, SQLModel e autenticação OAuth2/JWT.

O sistema trata dados relacionados à saúde e, portanto, exige controles de autenticação, autorização, validação de entrada, proteção contra vulnerabilidades da OWASP, persistência segura e integração de ferramentas DevSecOps.

O objetivo do Exercício 13 é demonstrar a rastreabilidade entre:

**Threat Model → vulnerabilidade → correção → teste → evidência → decisão de release.**

---

## 2. Escopo da auditoria

Foram avaliados:

- autenticação e emissão de tokens;
- autorização baseada em escopos OAuth2;
- autorização baseada em papéis;
- proteção contra BOLA;
- validação de entrada;
- prevenção de SQL Injection;
- prevenção de XSS;
- proteção contra Mass Assignment;
- CORS;
- Security Headers;
- persistência com SQLModel;
- dependências;
- instrumentação IAST;
- análise DAST com OWASP ZAP;
- testes automatizados com mocking;
- especificação OpenAPI;
- riscos residuais identificados por revisão manual.

---

## 3. Evidências coletadas

### 3.1 DAST — OWASP ZAP

Foi executado o OWASP ZAP em modo baseline/passivo contra a aplicação em execução.

Resultado:

| Resultado | Quantidade |
|---|---:|
| PASS | 65 |
| WARN | 2 |
| FAIL | 0 |
| INFO | 0 |

Relatório gerado:

`zap-exercicio13.html`

### 3.1.1 Alertas encontrados

#### 10049 — Storable and Cacheable Content

O ZAP identificou conteúdo armazenável/cacheável na resposta do endpoint raiz.

Classificação OWASP relacionada:

**A05:2021 — Security Misconfiguration**

No caso analisado, o endpoint raiz é um healthcheck que retorna apenas informações operacionais simples, não dados de saúde.

Para produção, recomenda-se definir explicitamente políticas de cache para endpoints que retornem dados sensíveis.

#### 90004 — Cross-Origin-Resource-Policy Header Missing or Invalid

O ZAP identificou ausência ou configuração inadequada do cabeçalho Cross-Origin-Resource-Policy.

Classificação OWASP relacionada:

**A05:2021 — Security Misconfiguration**

O sistema já possui outros controles de segurança HTTP, incluindo HSTS, X-Frame-Options e X-Content-Type-Options.

O alerta permanece como ponto de melhoria da configuração de segurança HTTP.

---

## 4. Testes automatizados com mocking

Foi criado:

`tests/test_exercicio13_mocking.py`

Foram implementados cinco testes utilizando `unittest.mock.MagicMock` e `pytest`.

Cenários:

1. rejeição de cadastro quando o e-mail já existe;
2. rejeição de acesso quando o usuário não possui ownership;
3. autorização do próprio paciente;
4. autorização do profissional relacionado à consulta;
5. autorização do administrador.

Resultado:

`5 passed, 1 warning`

O warning foi um `PytestCacheWarning` relacionado à criação do `.pytest_cache` no ambiente Windows e não causou falha nos testes.

---

## 5. Auditoria da especificação OpenAPI

Foi gerado:

`openapi-exercicio13.json`

A especificação contém 11 endpoints.

O mecanismo OAuth2PasswordBearer está documentado com:

- `read:horarios_disponiveis`;
- `read:consultas`;
- `write:consultas`;
- `admin`.

### 5.1 Endpoints corretamente documentados com escopos

- `GET /consultas/horarios-disponiveis`
- `GET /consultas/`
- `POST /consultas/`

### 5.2 Endpoints protegidos sem escopo explícito

- `GET /consultas/{consulta_id}`
- `GET /pacientes/{paciente_id}/prontuario`
- `GET /admin/relatorio-sistema`

Esses endpoints possuem proteção no código por dependências como `obter_usuario_atual`, `verificar_ownership` e `exigir_papel`, porém esses requisitos adicionais não são totalmente representados na OpenAPI.

No caso administrativo, o código exige efetivamente o papel `ADMIN`, embora a OpenAPI apresente somente OAuth2 genérico.

### 5.3 Endpoints públicos identificados

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/m2m/token`
- `GET /consultas/agenda-html`
- `GET /profissionais/`
- `POST /profissionais/`
- `GET /`

Os endpoints de autenticação e healthcheck possuem justificativa funcional para serem públicos.

Entretanto, `POST /profissionais/` deve ser revisado porque permite criação de registros sem autenticação ou autorização.

---

## 6. Rastreabilidade com o Threat Model

O Threat Model identificou como principais vetores:

- acesso não autorizado;
- BOLA;
- falhas de autenticação;
- falhas de autorização;
- abuso de escopos OAuth2;
- SQL Injection;
- XSS;
- manipulação de entradas;
- exposição de dados sensíveis;
- vulnerabilidades de dependências;
- abuso de endpoints de autenticação.

### 6.1 SQL Injection

**Threat Model:** manipulação maliciosa de consultas.

**Correção:** SQLModel/SQLAlchemy e consultas parametrizadas.

**Evidência:** testes do Exercício 9 e pipeline SAST/SCA.

**OWASP:** A03:2021 — Injection.

### 6.2 BOLA em consultas

**Threat Model:** usuário acessando objeto pertencente a outro usuário.

**Correção:** `verificar_ownership()` valida paciente, profissional ou administrador.

**Evidência:** testes de autorização e testes de mocking.

**OWASP:** A01:2021 — Broken Access Control.

### 6.3 BOLA em prontuário

**Threat Model:** acesso indevido a dados médicos de outro paciente.

**Correção:** paciente somente pode acessar seu próprio prontuário.

**Evidência:** `routes/paciente_routes.py`.

**OWASP:** A01:2021 — Broken Access Control.

**Risco residual:** a autorização de profissionais deve ser revisada para garantir vínculo legítimo com o paciente.

### 6.4 Stored XSS

**Threat Model:** armazenamento de conteúdo malicioso e posterior execução.

**Correção:** validação de entrada e Jinja2 com autoescape.

**Evidência:** testes do Exercício 9 e ZAP.

**OWASP:** A03:2021 — Injection.

### 6.5 Mass Assignment

**Threat Model:** envio de campos não autorizados.

**Correção:** schemas específicos e rejeição de campos adicionais.

**Evidência:** testes do Exercício 9.

**OWASP:** A01:2021 — Broken Access Control.

### 6.6 OAuth2 e escopos

**Threat Model:** abuso de privilégios.

**Correção:** OAuth2PasswordBearer, escopos específicos e validação dos escopos presentes no JWT.

**Evidência:** `security.py`, testes M2M e OpenAPI.

**OWASP:** A01:2021 — Broken Access Control.

### 6.7 MFA administrativo

**Threat Model:** comprometimento de contas privilegiadas.

**Correção:** MFA obrigatório para administradores.

**Evidência:** `routes/auth_routes.py` e testes de segurança.

**OWASP:** A07:2021 — Identification and Authentication Failures.

### 6.8 Security Headers e CORS

**Threat Model:** exploração do navegador e requisições de origens não autorizadas.

**Correção:** allowlist CORS, HSTS, X-Frame-Options e X-Content-Type-Options.

**Evidência:** `main.py` e ZAP.

**OWASP:** A05:2021 — Security Misconfiguration.

### 6.9 Dependências

**Threat Model:** vulnerabilidades conhecidas em componentes externos.

**Correção:** `pip-audit` integrado ao pipeline.

**Evidência:** job SCA do GitHub Actions.

**OWASP:** A06:2021 — Vulnerable and Outdated Components.

### 6.10 IAST

**Threat Model:** necessidade de observar a aplicação durante execução.

**Correção:** instrumentação de runtime em `iast.py` e middleware.

**Evidência:** `iast-runtime.log`.

---

## 7. Matriz de rastreabilidade

| ID | Risco | OWASP | Correção | Evidência | Status |
|---|---|---|---|---|---|
| V01 | SQL Injection | A03 | SQLModel/queries parametrizadas | Testes + SAST | Corrigido |
| V02 | BOLA em consulta | A01 | Ownership | Testes + mocking | Corrigido |
| V03 | BOLA em prontuário | A01 | Controle de paciente | Código + testes | Parcial |
| V04 | Stored XSS | A03 | Validação + Jinja2 | Testes + ZAP | Corrigido |
| V05 | Mass Assignment | A01 | Schemas + validação | Testes | Corrigido |
| V06 | Abuso de escopos M2M | A01 | OAuth2 scopes | Testes M2M | Corrigido |
| V07 | Autoelevação para ADMIN | A01 | Ainda não corrigido | Revisão manual | **Aberto** |
| V08 | Segredo M2M hardcoded | A07 | Ainda não corrigido | Revisão manual | **Aberto** |
| V09 | Ausência de rate limiting | A07 | Ainda não implementado | Revisão manual | **Aberto** |
| Z01 | Cacheabilidade | A05 | Avaliar política de cache | ZAP | Atenção |
| Z02 | CORP ausente | A05 | Avaliar header | ZAP | Atenção |

---

## 8. Riscos residuais

### 8.1 Autoelevação para ADMIN

O endpoint público de registro aceita o campo `papel`.

Isso pode permitir que um cliente solicite o papel `ADMIN` durante o cadastro.

**Classificação:** Critical.

**OWASP:** A01:2021 — Broken Access Control.

**Decisão:** BLOQUEAR RELEASE.

### 8.2 Credencial M2M no código

O `client_secret` M2M está diretamente definido no código-fonte.

**Classificação:** High.

**OWASP:** A07:2021 — Identification and Authentication Failures.

**Decisão:** BLOQUEAR RELEASE.

Recomenda-se variável de ambiente ou secret manager e rotação da credencial.

### 8.3 Ausência de rate limiting

O endpoint de login não possui limitação de tentativas.

**Classificação:** High.

**OWASP:** A07:2021 — Identification and Authentication Failures.

**Decisão:** BLOQUEAR RELEASE.

### 8.4 Listagem ampla de consultas

`GET /consultas/` retorna todas as consultas para usuários com `read:consultas`.

Em uma aplicação que processa dados de saúde, o princípio do menor privilégio exige filtragem adequada.

**OWASP:** A01:2021 — Broken Access Control.

**Decisão:** BLOQUEAR RELEASE até revisão.

### 8.5 Criação de consultas

`POST /consultas/` exige `write:consultas`, mas não demonstra validação de ownership sobre os `paciente_id` e `profissional_id` enviados.

**OWASP:** A01:2021 — Broken Access Control.

**Decisão:** BLOQUEAR RELEASE até revisão da regra de negócio.

### 8.6 Criação pública de profissionais

`POST /profissionais/` está sem autenticação ou autorização.

**OWASP:** A01:2021 — Broken Access Control.

**Decisão:** BLOQUEAR RELEASE até definição explícita da política.

### 8.7 Cross-Origin-Resource-Policy

O ZAP identificou ausência/configuração inadequada de CORP.

**OWASP:** A05:2021 — Security Misconfiguration.

**Decisão:** melhoria recomendada; não é o principal motivo para bloquear o release.

---

## 9. Avaliação final do Security Gate

Resultados automatizados:

- SAST: aprovado;
- SCA: aprovado;
- testes de segurança: aprovados;
- testes de mocking: 5/5 aprovados;
- IAST: evidência gerada;
- DAST/ZAP: 0 FAIL;
- OpenAPI: auditada.

Apesar dos resultados automatizados positivos, a revisão manual identificou riscos High e Critical relacionados a autorização, autenticação e gerenciamento de credenciais.

Ferramentas automatizadas não substituem testes de lógica de negócio e revisão manual de controle de acesso.

### Decisão final

# RELEASE BLOQUEADO

A aplicação não deve ser considerada pronta para produção enquanto os riscos críticos e altos não forem tratados.

---

## 10. Plano de correção prioritário

### Prioridade crítica

1. Impedir que o registro público permita criação de usuários ADMIN.
2. Restringir a atribuição do papel ADMIN a fluxo administrativo autorizado.

### Prioridade alta

3. Remover o segredo M2M do código.
4. Utilizar variável de ambiente ou secret manager.
5. Rotacionar a credencial atual.
6. Implementar rate limiting no login.
7. Revisar `GET /consultas/`.
8. Revisar `POST /consultas/`.
9. Restringir `POST /profissionais/`.

### Prioridade complementar

10. Definir política explícita de cache.
11. Adicionar/configurar CORP.
12. Melhorar a documentação dos requisitos de autorização na OpenAPI.

---

## 11. Conclusão

A aplicação apresenta evolução significativa de segurança em relação às vulnerabilidades identificadas nos exercícios anteriores.

Foram implementados controles de autenticação, autorização, OAuth2, MFA, ownership, validação de entrada, prevenção de SQL Injection, prevenção de XSS, CORS, Security Headers, persistência segura e ferramentas DevSecOps.

As evidências demonstram rastreabilidade entre o threat model, vulnerabilidades, correções e testes.

Entretanto, a auditoria final demonstrou que um pipeline DevSecOps aprovado não significa ausência absoluta de vulnerabilidades.

Como a aplicação processa dados de saúde, vulnerabilidades Critical e High relacionadas a controle de acesso, autenticação e proteção de dados devem bloquear o lançamento.

**Recomendação final: NÃO LIBERAR PARA PRODUÇÃO neste estado.**

Após a correção dos riscos identificados, a aplicação deverá passar novamente pelos testes automatizados, DAST, IAST e Security Gate antes da liberação.
