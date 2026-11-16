# Verificação da versão

- 10 testes automatizados de modelo e integração HTTP aprovados. Saída em `TEST_RESULTS.txt`.
- Sintaxe do JavaScript verificada com `node --check static/app.js`.
- Conferência manual no Chrome desktop: catálogo carregado, adição à sacola, formulário com nome e telefone, pedido registrado por R$ 14,00 e consulta retornando o status do pedido persistido.
- Layout responsivo implementado com breakpoints em CSS. Não foi realizada execução em aparelho móvel físico.
- Não foram testadas cobranças: esta versão registra pedidos para pagamento na retirada.

O banco usado no teste manual não acompanha a entrega; a primeira execução cria um banco limpo com os seis sabores e 40 unidades de cada.
