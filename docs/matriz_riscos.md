# Matriz de Riscos de Segurança

## Critério de priorização

A priorização das vulnerabilidades foi realizada utilizando o CVSS v3.1 em conjunto com o impacto de negócio para a aplicação.

Como a aplicação processa dados pessoais e dados sensíveis relacionados à saúde, vulnerabilidades que possam permitir acesso indevido, alteração ou exposição dessas informações possuem prioridade elevada.

### Critério do Security Gate

O pipeline será bloqueado quando forem identificadas vulnerabilidades classificadas como:

- **Critical**
- **High**

Vulnerabilidades **Medium** e **Low** serão registradas como alertas e não bloquearão o pipeline automaticamente.

Além da severidade técnica, o impacto sobre a confidencialidade, integridade e disponibilidade dos dados de saúde será considerado na priorização.

---

## Matriz de vulnerabilidades

| ID | Vulnerabilidade | Origem | CVSS | Severidade | Impacto de negócio | Security Gate | Situação |
|---|---|---|---:|---|---|---|---|
| V01 | SQL Injection | Exercícios 8 e 11 | 9.8 | Critical | Pode permitir acesso, alteração ou destruição de dados do sistema | BLOQUEIA | Corrigida |
| V02 | BOLA em consultas | Exercícios 6 e 9 | 6.5 | High | Paciente pode acessar dados de consultas pertencentes a outro paciente | BLOQUEIA | Corrigida |
| V03 | BOLA em prontuário | Exercício 9 | 6.5 | High | Exposição indevida de dados sensíveis de saúde | BLOQUEIA | Corrigida |
| V04 | Stored XSS | Exercícios 8 e 9 | 5.4 | Medium | Possível execução de JavaScript no contexto da aplicação e comprometimento de sessão | ALERTA | Corrigida |
| V05 | Mass Assignment / campos não declarados | Exercício 9 | 6.5 | Medium | Um atacante poderia tentar alterar propriedades não previstas pela API | ALERTA | Corrigida |
| V06 | Abuso de escopos OAuth2/M2M | Exercício 6 e testes M2M | 8.1 | High | Cliente externo poderia tentar obter acesso a recursos além de sua autorização | BLOQUEIA | Protegida |
| V07 | Escalonamento indevido de privilégio no cadastro | Assessment | 9.8 | Critical | Usuário poderia tentar criar uma conta administrativa e obter privilégios elevados | BLOQUEIA | A validar |
| V08 | Credencial M2M armazenada diretamente no código | Assessment | 7.5 | High | Vazamento da credencial poderia permitir autenticação indevida de um sistema parceiro | BLOQUEIA | A corrigir |
| V09 | Ausência de rate limiting no login | Exercício 10 | 7.5 | High | Facilita ataques de força bruta e tentativa automatizada de credenciais | BLOQUEIA | A implementar |
| V10 | Ausência de headers de segurança / CORS inadequado | Exercício 10 | 4.3 | Medium | Pode aumentar a superfície de ataque do navegador e permitir comportamentos indevidos | ALERTA | Corrigida |

---

## Justificativa das principais vulnerabilidades

### V01 — SQL Injection

A SQL Injection foi considerada Critical devido à possibilidade de manipulação das consultas ao banco de dados.

O problema foi tratado utilizando SQLModel e consultas parametrizadas, evitando a concatenação de valores fornecidos pelo usuário diretamente em comandos SQL.

Também foi criado um teste utilizando uma entrada maliciosa para verificar se a consulta poderia ser manipulada.

---

### V02 — BOLA em consultas

A vulnerabilidade BOLA (Broken Object Level Authorization) ocorre quando um usuário consegue acessar um objeto pertencente a outro usuário apenas modificando seu identificador.

No contexto da aplicação, isso poderia permitir que um paciente acessasse uma consulta pertencente a outro paciente.

A vulnerabilidade recebeu prioridade High porque consultas podem conter informações pessoais e relacionadas à saúde.

O controle de ownership foi implementado e testado no Exercício 9.

---

### V03 — BOLA em prontuário

O prontuário contém informações sensíveis de saúde e, portanto, possui impacto elevado sobre a confidencialidade.

O teste de segurança verifica que um paciente não consegue acessar o prontuário de outro paciente.

A aplicação deve retornar HTTP 403 quando o usuário não possuir autorização para acessar o recurso.

---

### V04 — Stored XSS

Foi considerada a possibilidade de armazenamento de conteúdo malicioso enviado pelo usuário e posterior renderização desse conteúdo na aplicação.

A aplicação passou a utilizar validação de entrada e mecanismos de escape/autoescape no conteúdo HTML.

O teste de segurança verifica que uma carga contendo JavaScript não é aceita pela API.

---

### V05 — Mass Assignment

A API foi protegida contra o envio de campos não declarados nos modelos de entrada.

Foi utilizado:

```python
model_config = ConfigDict(extra="forbid")