# Verificação da versão corrigida

## Antes da correção

Na versão anterior do GitHub/Render, a análise técnica identificou três problemas: telefone com letras aceito, confirmação antiga escondendo nova sacola e ausência de acesso ao pedido após recarregar a página.

## Depois da correção

- 16 testes Python de modelo e integração HTTP aprovados. Incluem novos casos para formatos de telefone, normalização, recuperação do último pedido após reinicialização do modelo e isolamento entre sessões.
- 5 testes de regressão JavaScript aprovados, usando DOM e rede simulados. Cobrem bloqueio do telefone antes do POST, segunda compra, recuperação do pedido após recarga, sessão sem pedidos e redução de quantidade quando o estoque diminui.
- Conferência manual no Chrome, em servidor local com a versão corrigida: telefone `11999999999abc` bloqueado com mensagem; telefone formatado aceito; confirmação de pedido com itens e total; nova adição e reabertura da sacola exibindo o novo carrinho; recarga seguida de “Último pedido” recuperando o protocolo e os itens anteriores.
- Os testes manuais foram executados em ambiente local, sem publicar alterações no GitHub ou no Render.
- Não houve teste em aparelho móvel físico. O CSS responsivo existente foi mantido e o espaçamento dos botões foi ajustado para telas estreitas.
- Não houve teste de cobrança, pois o projeto utiliza pagamento na retirada.

O banco de testes não acompanha a entrega. Não apague o banco existente para instalar as correções.

A validação do telefone verifica formato, não titularidade nem existência da linha. O último pedido depende da sessão do navegador e de o registro ainda existir no banco. A correção não elimina as limitações de armazenamento do Render gratuito.

Esta é uma verificação técnica assistida, não um relato de participação dos cinco colegas exigidos pelo trabalho.

## Fotos locais

As seis imagens fornecidas foram incorporadas em `static/images` e associadas aos respectivos sabores. O teste HTTP confirma tipo PNG, conteúdo e rejeição de caminhos não permitidos. No Chrome, foi confirmado o carregamento das seis fotos do catálogo e da foto do destaque a partir do próprio servidor local.
