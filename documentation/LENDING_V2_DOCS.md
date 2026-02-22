# API de Comodatos V2

Esta documentação descreve a V2 da API de Comodatos, que introduz um fluxo mais eficiente para a criação de comodatos, incluindo o upload de anexos e a geração de contratos em uma única requisição.

## Endpoint Principal

### `POST /api/v2/lendings/`

Este endpoint orquestra a criação de um novo comodato, o upload de arquivos anexos e a geração do documento de contrato correspondente. Ele foi projetado para simplificar o processo, que antes exigia múltiplas chamadas de API.

#### Estrutura da Requisição

A requisição deve ser do tipo `multipart/form-data` e conter os seguintes campos:

-   `data` (JSON string): String JSON contendo o objeto que segue o schema `NewLendingDataSchema`.
-   `attachments` (array de `UploadFile`, opcional): Lista de arquivos a serem anexados ao comodato.

Exemplo de envio com `curl`:

```bash
curl -X POST "http://localhost:8080/api/v2/lendings/" \
  -H "Authorization: Bearer <TOKEN>" \
  -F 'data={"employeeId":1,"assetId":1,"workloadId":1,"costCenterId":1,"manager":"Gestor","location":"Salvador - BA","bu":"ADS","principalSigner":"principal@solutis.com.br","employeeSigner":"employee@solutis.com.br","businessExecutive":"Executivo","witnessesId":[2,3],"msOffice":false,"legalPerson":false}' \
  -F "attachments=@/caminho/arquivo1.pdf" \
  -F "attachments=@/caminho/arquivo2.pdf"
```

#### Exemplo de `data`

```json
{
    "employeeId": 1,
    "assetId": 1,
    "workloadId": 1,
    "costCenterId": 1,
    "manager": "Nome do Gestor",
    "observations": "Observações sobre o comodato",
    "glpiNumber": "12345",
    "businessExecutive": "Executivo de Negócios",
    "project": "Nome do Projeto",
    "location": "Localização",
    "bu": "ADS",
    "msOffice": true,
    "principalSigner": "email.principal@signer.com",
    "employeeSigner": "email.employee@signer.com",
    "witnessesId": [2, 3],
    "legalPerson": false,
    "verificationAnswers": {
        "typeId": 1,
        "answered": [
            {
                "verificationId": 10,
                "answer": "Sim",
                "observations": "Conforme combinado"
            }
        ]
    }
}
```

#### Resposta

-   **201 Created**: Retorna um objeto JSON contendo os dados do comodato, do documento e das respostas de verificacao (quando enviadas).
    ```json
    {
        "lending": {
            "id": 1,
            "employee": { ... },
            "asset": { ... },
            ...
        },
        "document": {
            "id": 1,
            "path": "/path/to/document.pdf",
            ...
        },
        "verfication": [
            { "id": 99, "verificationId": 10, "answer": "Sim" }
        ]
    }
    ```
-   **400 Bad Request**: Ocorre se o JSON em `data` for invalido.
-   **401 Unauthorized**: Se o usuário não estiver autenticado ou não tiver permissão para criar comodatos.

## Arquitetura

### `LendingController`

A lógica de orquestração foi centralizada na classe `LendingController`. Esta classe é responsável por:

1.  **Autenticação**: Verificar se o usuário está autenticado.
2.  **Criação do Comodato**: Chamar `LendingService.create_lending` para criar o registro do comodato no banco de dados.
3.  **Upload de Anexos**: Iterar sobre os arquivos enviados e usar `LendingAttachmentService.upload_attachment` para salvá-los.
4.  **Criação do Contrato**: Chamar `DocumentService.create_contract` para gerar o PDF do contrato.
5.  **Respostas de Verificacao**: Se informado, chamar `VerificationService.create_answer_verification`.

### `router_v2.py`

O novo arquivo de rotas (`router_v2.py`) define o endpoint `/api/v2/lendings/`. Ele utiliza `FastAPI` para receber `data` e `attachments` no `multipart/form-data`, e injeta o `LendingController` para executar o fluxo de negocio.
