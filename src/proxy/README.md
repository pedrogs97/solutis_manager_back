# Proxy Service - Multi-Service Support

Este módulo implementa um serviço proxy que permite fazer requisições para **múltiplos serviços externos** com validação de permissões integrada ao sistema de autenticação existente.

## Configuração

### Variáveis de Ambiente

Adicione as seguintes variáveis de ambiente ao seu arquivo `.env`:

```env
# URLs dos serviços (obrigatório)
PROCUREMENT_SERVICE_HOST=http://procurement-api.example.com
EXTERNAL_SERVICE_HOST=http://fallback-api.example.com  # serviço padrão/fallback

# Timeout para requisições em segundos (opcional, padrão: 30)
EXTERNAL_SERVICE_TIMEOUT=30

# Número de tentativas em caso de falha (opcional, padrão: 3)
EXTERNAL_SERVICE_RETRY_ATTEMPTS=3
```

## Funcionalidades

### Suporte a Múltiplos Serviços

O proxy agora suporta redirecionamento para diferentes serviços baseado no nome do serviço na URL:

- **procurement**: Para o serviço de procurement (`PROCUREMENT_SERVICE_HOST`)
- **default**: Serviço padrão/fallback (`EXTERNAL_SERVICE_HOST`)

### Validação de Permissões

O proxy utiliza o sistema `PermissionChecker` existente para validar permissões antes de fazer requisições ao serviço externo. As permissões são organizadas por tipo de operação:

- **read**: Para operações GET (permissão: `proxy.external_service.read`)
- **write**: Para operações POST, PUT, PATCH (permissão: `proxy.external_service.write`)
- **admin**: Para operações DELETE (permissão: `proxy.external_service.admin`)

### Endpoints Disponíveis

O proxy expõe os seguintes endpoints:

- `GET /api/v1/{service_name}/{path:path}` - Proxy para requisições GET
- `POST /api/v1/{service_name}/{path:path}` - Proxy para requisições POST
- `PUT /api/v1/{service_name}/{path:path}` - Proxy para requisições PUT
- `PATCH /api/v1/{service_name}/{path:path}` - Proxy para requisições PATCH
- `DELETE /api/v1/{service_name}/{path:path}` - Proxy para requisições DELETE
- `GET /api/v1/{service_name}/health` - Verificação de saúde do proxy e serviço específico

### Funcionalidades de Segurança

1. **Filtragem de Headers**: Apenas headers específicos são encaminhados ao serviço externo
2. **Validação de Autenticação**: Todas as requisições requerem token JWT válido
3. **Controle de Permissões**: Diferentes níveis de permissão para diferentes tipos de operação
4. **Validação de Serviços**: Apenas serviços configurados são aceitos
5. **Retry Logic**: Tentativas automáticas em caso de falha de conexão
6. **Timeout**: Controle de timeout para evitar requisições presas

## Uso

### Exemplo de Requisições

```bash
# GET request para o serviço de procurement
curl -X GET \
  http://localhost:8000/api/v1/procurement/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# POST request para o serviço de procurement
curl -X POST \
  http://localhost:8000/api/v1/procurement/orders \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product": "Laptop", "quantity": 5}'

# Usando o serviço padrão
curl -X GET \
  http://localhost:8000/api/v1/default/status \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Verificação de Saúde

```bash
# Health check do serviço de procurement
curl -X GET \
  http://localhost:8000/api/v1/procurement/health \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Health check do serviço padrão
curl -X GET \
  http://localhost:8000/api/v1/default/health \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Resposta esperada:
```json
{
  "proxy_status": "healthy",
  "service_name": "procurement",
  "external_service_status": "healthy",
  "external_service_response_code": 200
}
```

## Adicionando Novos Serviços

Para adicionar um novo serviço ao proxy:

1. **Adicione a variável de ambiente**:
   ```env
   NEW_SERVICE_HOST=http://new-service.example.com
   ```

2. **Atualize o config.py**:
   ```python
   SERVICE_HOSTS = {
       "procurement": os.getenv("PROCUREMENT_SERVICE_HOST", "http://localhost:8001"),
       "new_service": os.getenv("NEW_SERVICE_HOST", "http://localhost:8002"),
       "default": os.getenv("EXTERNAL_SERVICE_HOST", "http://localhost:8001"),
   }
   ```

3. **Use o novo serviço**:
   ```bash
   curl -X GET http://localhost:8000/api/v1/new_service/endpoint
   ```

## Configuração de Permissões

Para que o proxy funcione corretamente, é necessário criar as permissões no sistema:

1. **proxy.external_service.read** - Para operações de leitura
2. **proxy.external_service.write** - Para operações de escrita
3. **proxy.external_service.admin** - Para operações administrativas

Essas permissões devem ser atribuídas aos grupos de usuários conforme necessário.

## Headers Encaminhados

Os seguintes headers são automaticamente encaminhados ao serviço externo:

- `authorization`
- `content-type`
- `accept`
- `user-agent`
- `x-requested-with`

## Tratamento de Erros

O proxy trata automaticamente os seguintes tipos de erro:

- **400 Bad Request**: Nome de serviço inválido
- **502 Bad Gateway**: Erro de conexão com o serviço externo
- **504 Gateway Timeout**: Timeout na comunicação com o serviço externo
- **403 Forbidden**: Permissões insuficientes
- **500 Internal Server Error**: Erro interno do proxy

## Logs

O proxy gera logs detalhados das operações, incluindo:

- Tentativas de requisição com nome do serviço
- Status codes de resposta
- Erros de conexão
- Timeouts
- Serviços acessados

## Exemplos de Uso por Serviço

### Procurement Service

```bash
# Listar fornecedores
GET /api/v1/procurement/suppliers

# Criar ordem de compra
POST /api/v1/procurement/purchase-orders

# Atualizar contrato
PUT /api/v1/procurement/contracts/123

# Deletar requisição
DELETE /api/v1/procurement/requests/456
```

### Serviço Padrão

```bash
# Qualquer endpoint do serviço padrão
GET /api/v1/default/any-endpoint
POST /api/v1/default/data
```

O proxy oferece uma solução robusta e escalável para integração com múltiplos serviços externos mantendo a segurança e controle de acesso do sistema principal.
