# Petit — loja de cupcakes

Aplicação MVC em Python 3.10+ com SQLite e interface em HTML, CSS e JavaScript puro. Sem dependências Python externas. O banco é criado e populado automaticamente na primeira execução.
 
## Acesso online

A aplicação está hospedada no Render e pode ser acessada pelo navegador, sem instalação de Python ou uso de terminal.

Link: [https://petit-cupcakes.onrender.com]

A hospedagem utiliza o plano gratuito. O primeiro acesso após um período de inatividade pode demorar. Os pedidos e as alterações de estoque armazenados no SQLite podem ser perdidos quando o serviço reinicia ou entra em suspensão.

## Executar localmente

1. Instale Python 3.10 ou superior.
2. Extraia o ZIP e abra um terminal na pasta `cupcake-shop`.
3. Execute `python app.py` (no Windows, `py app.py` também funciona).
4. Abra http://localhost:8000 no navegador.

Não abra `index.html` diretamente: o servidor fornece a interface e as APIs.

## Testar

```sh
python -m unittest discover -s tests -v
```

A suíte cobre persistência, cálculo de preços no servidor, repetição de checkout sem duplicação, isolamento de pedidos por cookie, validação de entradas, rollback, concorrência de estoque, arquivos da interface, fluxo HTTP de compra e erros HTTP. JavaScript pode ser verificado com `node --check static/app.js` (Node é opcional).

## O que funciona

- Catálogo de seis cupcakes, filtros por categoria, preços em reais e estoque.
- Interface responsiva, navegação por teclado, diálogo nativo, mensagens de estado e campos rotulados.
- Carrinho com alteração e remoção de itens, salvo neste navegador.
- Checkout com nome e telefone, validação no cliente e no servidor.
- Pedidos e itens persistidos no SQLite; valores monetários em centavos inteiros.
- Estoque atualizado em transação atômica, sem venda acima do estoque em requisições simultâneas.
- Chave de idempotência para repetição de requisições sem duplicar o mesmo pedido.
- Consulta do pedido pela sessão original, sem expor pedidos de outro navegador.
- Tratamento de erros 400, 403, 404, 413, 415 e 500.
- SQL parametrizado, cookie HttpOnly/SameSite, política de conteúdo e rotas de arquivos permitidas explicitamente.

## Arquitetura MVC

| Camada | Arquivos | Responsabilidade |
| --- | --- | --- |
| Model | `models/store.py` | Esquema, catálogo, transações, estoque e persistência dos pedidos |
| View | `views/index.html`, `static/style.css`, `static/app.js` | Interface, carrinho e comunicação HTTP |
| Controller | `controllers/shop.py` | Rotas, sessão, validação de requisições e respostas |
| Entrada | `app.py` | Configuração e inicialização do servidor |

O estado do catálogo e dos pedidos é do servidor. O navegador envia IDs e quantidades; o servidor ignora preços enviados pelo cliente. Os itens guardam o nome e preço no momento da compra.

## API

| Método | Rota | Resultado |
| --- | --- | --- |
| GET | `/api/products` | Catálogo e estoque |
| POST | `/api/orders` | Registra pedido e atualiza estoque |
| GET | `/api/orders/{token}` | Consulta pedido da mesma sessão |

O POST requer `Content-Type: application/json`, `X-Shop-Request: checkout` e um corpo como:

```json
{"name":"Ana Silva","phone":"11999999999","key":"identificador-unico-de-16-a-100-caracteres","cart":{"1":2,"3":1}}
```

Use uma chave diferente por compra; preserve-a ao repetir uma tentativa após falha de conexão. O cookie `shop` precisa ser mantido entre as requisições.

## Banco e configuração

`shop.sqlite3` é criado ao lado de `app.py`. Não há banco com dados pessoais no pacote. Para um banco em outro caminho, configure `DATABASE_PATH`. Faça backup antes de qualquer manutenção. Os sabores e quantidades iniciais estão em `models/store.py`; alterações nessa lista só se aplicam a um banco novo. A gestão administrativa não faz parte desta versão; ajustes de catálogo e estoque exigem manutenção do banco.

Variáveis opcionais: `HOST` (padrão `127.0.0.1`), `PORT` (8000), `DATABASE_PATH`, `COOKIE_SECURE=1` para cookies em HTTPS. Reiniciar o servidor preserva os pedidos no arquivo SQLite. Apagar cookies impede consultar pedidos da sessão antiga. O protocolo não é uma conta de usuário.

## Limites e implantação

Esta é uma loja demonstrativa funcional para pedidos com pagamento na retirada. Não inclui cobrança online, integração Pix/cartão, cálculo de frete, entrega, mensagens automáticas, painel administrativo nem atualização de status. O status permanece “Recebido”. Não há endereço, horário ou identidade comercial reais configurados. Não anuncie que o produto será entregue sem confirmar esses dados com o cliente.

O servidor HTTP da biblioteca padrão é adequado para execução e avaliação local. Para operação comercial na internet, é necessário adaptar a camada HTTP a um servidor de produção, configurar HTTPS, limites de requisição, monitoramento, backups, política de privacidade/LGPD e dados reais da loja. O projeto está publicado no Render para demonstração acadêmica, com back-end Python e banco SQLite.

As ilustrações são SVG originais incorporados à interface e funcionam sem serviços externos. Não representam fotografias dos produtos reais.
