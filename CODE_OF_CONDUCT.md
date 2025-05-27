[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Educational Purpose](https://img.shields.io/badge/Purpose-Educational-blue.svg)]()

# Guia de Contribuição

## 🎓 Propósito Educacional

Este projeto foi criado **exclusivamente para fins educacionais e de aprendizado**. O objetivo principal é demonstrar e ensinar conceitos de desenvolvimento de software com Python, incluindo:

- APIs REST com FastAPI
- Autenticação e autorização
- Integração com APIs externas
- Processamento assíncrono
- Arquitetura de software

## ⚠️ Importante: Uso Educacional Apenas

**ESTE PROJETO NÃO DEVE SER USADO PARA:**
- Download de conteúdo protegido por direitos autorais
- Violação de termos de serviço de plataformas
- Qualquer atividade comercial ou de distribuição de conteúdo

**ESTE PROJETO DEVE SER USADO PARA:**
- Aprender sobre desenvolvimento Python
- Estudar padrões de arquitetura de APIs
- Compreender conceitos de autenticação e segurança
- Explorar integração com APIs externas
- Experimentar com processamento paralelo

## 🤝 Como Contribuir Educacionalmente

### Tipos de Contribuições Aceitas

1. **Melhorias na Documentação**
   - Explicações mais detalhadas de conceitos
   - Comentários de código mais informativos
   - Exemplos educacionais adicionais
   - Correções de gramática e ortografia

2. **Melhorias no Código para Fins Educacionais**
   - Refatoração para melhor legibilidade
   - Implementação de melhores práticas
   - Otimizações de performance
   - Correções de bugs

3. **Recursos Educacionais**
   - Tutoriais passo a passo
   - Diagramas de arquitetura
   - Explicações de conceitos técnicos
   - Exemplos de uso educacional

4. **Melhorias na Estrutura do Projeto**
   - Melhor organização de arquivos
   - Configurações de desenvolvimento
   - Scripts de automação educacionais
   - Testes unitários e de integração

### O Que NÃO Aceitamos

- Contribuições que visem facilitar download de conteúdo protegido
- Melhorias focadas em contornar limitações de APIs
- Recursos que incentivem uso comercial ou ilegal
- Modificações que removam avisos educacionais

## 📋 Processo de Contribuição

### 1. Preparação

1. Fork o repositório
2. Clone seu fork localmente
3. Crie um ambiente virtual Python
4. Instale as dependências de desenvolvimento

```bash
git clone https://github.com/seu-usuario/spotify-downloader-api.git
cd spotify-downloader-api
python -m venv venv
source venv/bin/activate  # Linux/macOS ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 2. Desenvolvimento

1. Crie uma branch para sua contribuição:
```bash
git checkout -b feature/nome-da-sua-contribuicao
```

2. Faça suas alterações seguindo as diretrizes:
   - Mantenha o foco educacional
   - Adicione comentários explicativos
   - Inclua documentação quando necessário
   - Teste suas alterações

3. Commit suas alterações com mensagens descritivas:
```bash
git commit -m "docs: adiciona explicação sobre autenticação JWT"
```

### 3. Submissão

1. Push sua branch:
```bash
git push origin feature/nome-da-sua-contribuicao
```

2. Abra um Pull Request com:
   - Título claro e descritivo
   - Descrição detalhada das alterações
   - Explicação do valor educacional
   - Screenshots/exemplos se aplicável

## 🔍 Diretrizes de Código

### Estilo de Código

- Siga as convenções PEP 8 para Python
- Use nomes descritivos para variáveis e funções
- Inclua docstrings em funções e classes
- Mantenha funções pequenas e focadas

### Comentários e Documentação

- Explique o "porquê", não apenas o "o que"
- Use comentários para conceitos educacionais
- Documente APIs e endpoints claramente
- Inclua exemplos de uso quando apropriado

### Exemplo de Função Bem Documentada

```python
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Autentica um usuário verificando suas credenciais.
    
    Esta função demonstra conceitos importantes de segurança:
    - Verificação de hash de senha usando bcrypt
    - Tratamento seguro de dados sensíveis
    - Retorno consistente independente do resultado
    
    Args:
        db: Sessão do banco de dados SQLAlchemy
        username: Nome de usuário fornecido
        password: Senha em texto plano (será verificada contra hash)
    
    Returns:
        User object se autenticação bem-sucedida, None caso contrário
        
    Educational Note:
        Nunca armazene senhas em texto plano. Sempre use funções
        de hash criptográficas como bcrypt, scrypt ou Argon2.
    """
    # Buscar usuário no banco de dados
    user = db.query(User).filter(User.username == username).first()
    
    # Verificar se usuário existe e senha está correta
    if not user or not verify_password(password, user.hashed_password):
        return None
    
    return user
```

## 🧪 Testes

- Inclua testes para suas contribuições quando apropriado
- Testes devem ser educacionais e demonstrar conceitos
- Use pytest como framework de testes
- Documente casos de teste complexos

## 📖 Recursos Educacionais

### Conceitos Abordados no Projeto

1. **FastAPI Framework**
   - Roteamento e endpoints
   - Middleware e CORS
   - Documentação automática
   - Validação de dados

2. **Autenticação e Segurança**
   - JSON Web Tokens (JWT)
   - Hash de senhas com bcrypt
   - OAuth 2.0 concepts
   - Controle de acesso baseado em roles

3. **Banco de Dados**
   - ORM com SQLAlchemy
   - Migrações de esquema
   - Relacionamentos entre tabelas
   - Consultas eficientes

4. **Processamento Assíncrono**
   - Filas de tarefas
   - Processamento paralelo
   - Gerenciamento de estado
   - Threading vs AsyncIO

### Recursos para Aprendizado

- [Documentação FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [JWT Introduction](https://jwt.io/introduction/)
- [Python AsyncIO](https://docs.python.org/3/library/asyncio.html)

## 🚨 Código de Conduta Educacional

### Nossos Compromissos

- Manter o foco educacional em todas as contribuições
- Respeitar direitos autorais e propriedade intelectual
- Promover boas práticas de desenvolvimento
- Criar um ambiente de aprendizado inclusivo

### Comportamentos Esperados

- Use linguagem inclusiva e respeitosa
- Seja paciente com iniciantes
- Forneça feedback construtivo
- Compartilhe conhecimento de forma generosa
- Respeite diferentes níveis de experiência

### Comportamentos Inaceitáveis

- Incentivo a atividades ilegais
- Linguagem ofensiva ou discriminatória
- Compartilhamento de conteúdo protegido
- Spam ou autopromoção excessiva

## 📞 Contato

Se você tem dúvidas sobre contribuições educacionais, pode:

1. Abrir uma issue no GitHub para discussão
2. Contactar os mantenedores do projeto
3. Participar das discussões educacionais

## 📝 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença MIT do projeto, mantendo sempre o foco educacional.

---

**Lembre-se:** Toda contribuição deve ter valor educacional e estar alinhada com o propósito de aprendizado do projeto. Juntos, podemos criar um recurso valioso para a comunidade de desenvolvedores Python!
