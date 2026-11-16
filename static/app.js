'use strict';
const $=s=>document.querySelector(s), money=n=>new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(n/100);
let products=[],category='Todos',cart={},pendingKey=null,busy=false;
try{const saved=JSON.parse(localStorage.getItem('petit-cart')||'{}');if(saved&&typeof saved==='object'&&!Array.isArray(saved))cart=Object.fromEntries(Object.entries(saved).filter(([id,q])=>/^\d+$/.test(id)&&Number.isInteger(q)&&q>0&&q<=30));pendingKey=localStorage.getItem('petit-key')}catch{}
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const productPhotos = {"1": "/static/images/red-velvet.png", "2": "/static/images/chocolate-intenso.png", "3": "/static/images/morango-dos-sonhos.png", "4": "/static/images/limao-siciliano.png", "5": "/static/images/doce-de-leite.png", "6": "/static/images/baunilha-confete.png"};
function photo(id,name,hero=false){return `<img src="${productPhotos[id]}" alt="${escape(name)}" loading="${hero?'eager':'lazy'}" decoding="async" referrerpolicy="no-referrer">`}
$('#hero-cake').innerHTML=photo(3,'Cupcake de morango',true);
function persist(){try{localStorage.setItem('petit-cart',JSON.stringify(cart));if(pendingKey)localStorage.setItem('petit-key',pendingKey);else localStorage.removeItem('petit-key')}catch{}}
function toast(msg){$('#toast').textContent=msg;$('#toast').classList.add('show');setTimeout(()=>$('#toast').classList.remove('show'),2300)}
function renderProducts(){const list=products.filter(p=>category==='Todos'||p.category===category);$('#products').innerHTML=list.map(p=>`<article class="product"><div class="product-image" style="--tile:${p.cream}55">${photo(p.id,p.name)}</div><h3>${escape(p.name)}</h3><p>${escape(p.description)}</p><div class="buy-row"><b>${money(p.price)}</b><button data-add="${p.id}" ${p.stock===0?'disabled':''}>${p.stock===0?'Esgotado':'Adicionar +'}</button></div><small class="stock">${p.stock} disponíveis</small></article>`).join('')}
function renderCart(){let total=0,count=0;$('#cart-items').innerHTML=Object.entries(cart).map(([id,q])=>{const p=products.find(p=>p.id===Number(id));if(!p)return '';total+=p.price*q;count+=q;return `<div class="cart-row"><div><b>${escape(p.name)}</b><small>${money(p.price)} cada</small></div><div class="quantity"><button data-change="${id}" data-delta="-1" aria-label="Diminuir ${escape(p.name)}">−</button><span>${q}</span><button data-change="${id}" data-delta="1" aria-label="Aumentar ${escape(p.name)}">+</button></div></div>`}).join('')||'<p>Sua sacola está esperando um pouco de doçura.</p>';$('#total').textContent=money(total);$('#count').textContent=count;$('#submit-order').disabled=!count||busy}
async function load(){const r=await fetch('/api/products');if(!r.ok)throw Error('Não foi possível carregar os sabores. Atualize a página.');products=await r.json();for(const id of Object.keys(cart))if(!products.some(p=>p.id===Number(id)))delete cart[id];renderProducts();renderCart();persist()}

// A confirmação do pedido e o carrinho têm visualizações independentes.
let latestOrder = null;
const phonePattern = /^(?:\([1-9][0-9]\)|[1-9][0-9]) ?(?:9[0-9]{4}|[2-5][0-9]{3})-?[0-9]{4}$/;
const phoneField = $('#checkout input[name="phone"]');
function validatePhone() {
  const valid = phonePattern.test(phoneField.value.trim());
  phoneField.setCustomValidity(valid ? '' : 'Informe um telefone válido com DDD, sem letras. Ex.: (11) 99999-9999.');
  return valid;
}
phoneField.addEventListener('input', validatePhone);

function openDialog() {
  if (!$('#cart-dialog').open) $('#cart-dialog').showModal();
}
function showCart() {
  $('#dialog-title').textContent = 'Sua sacola';
  $('#receipt').hidden = true;
  $('#checkout').hidden = false;
  $('#cart-items').hidden = false;
  $('.total').hidden = false;
  $('#checkout-error').textContent = '';
  renderCart();
}
function rememberOrder(order) {
  latestOrder = order;
  $('#last-order').hidden = !order;
}
async function loadLatestOrder() {
  const response = await fetch('/api/orders/latest');
  if (!response.ok) throw Error('Não foi possível consultar o último pedido.');
  const data = await response.json();
  rememberOrder(data.order);
  return data.order;
}
function showReceipt(order) {
  rememberOrder(order);
  $('#dialog-title').textContent = 'Seu pedido';
  $('#receipt').hidden = false;
  $('#checkout').hidden = true;
  $('#cart-items').hidden = true;
  $('.total').hidden = true;
  $('#receipt').innerHTML = `
    <p class="eyebrow">PEDIDO REGISTRADO ♡</p>
    <h2>Obrigado por escolher a Petit, ${escape(order.customer)}!</h2>
    <p>${escape(order.status)}</p>
    <ul class="receipt-items">${order.items.map(item => `<li>${item.quantity} × ${escape(item.name)} — ${money(item.price * item.quantity)}</li>`).join('')}</ul>
    <p><b>Total: ${money(order.total)}</b></p>
    <p>A loja deverá confirmar local e horário de retirada. Nenhum pagamento foi realizado.</p>
    <p class="muted">Protocolo: ${escape(order.token)}</p>
    <div class="order-actions"><button id="check-order" class="primary">Consultar pedido</button><button id="new-order" class="bag">Voltar à sacola</button></div>
    <p id="order-status" role="status"></p>
    <p class="muted">Você pode recuperar este pedido pelo botão “Último pedido” neste navegador, enquanto a sessão e o banco forem mantidos.</p>`;
  $('#check-order').onclick = async () => {
    const button = $('#check-order');
    button.disabled = true;
    try {
      const response = await fetch('/api/orders/' + encodeURIComponent(order.token));
      const data = await response.json();
      if (!response.ok) throw Error(data.error || 'Não foi possível consultar o pedido.');
      $('#order-status').textContent = data.status;
    } catch (error) {
      $('#order-status').textContent = error.message || 'Falha de conexão. Tente novamente.';
    } finally { button.disabled = false; }
  };
  $('#new-order').onclick = showCart;
}

$('.filters').addEventListener('click', event => {
  const button = event.target.closest('[data-category]');
  if (!button) return;
  category = button.dataset.category;
  document.querySelectorAll('[data-category]').forEach(item => item.classList.toggle('active', item === button));
  renderProducts();
});
$('#products').addEventListener('click', event => {
  const button = event.target.closest('[data-add]');
  if (!button || busy) return;
  const id = button.dataset.add, product = products.find(item => item.id === Number(id));
  if ((cart[id] || 0) >= Math.min(30, product.stock)) return toast('Limite de quantidade ou estoque atingido.');
  cart[id] = (cart[id] || 0) + 1;
  pendingKey = null;
  persist(); renderCart();
  toast('Uma delícia adicionada à sacola ♡');
});
$('#cart-items').addEventListener('click', event => {
  const button = event.target.closest('[data-change]');
  if (!button || busy) return;
  const id = button.dataset.change, product = products.find(item => item.id === Number(id));
  const delta = Number(button.dataset.delta), quantity = cart[id] + delta;
  // Mesmo se o estoque cair, o cliente ainda deve conseguir reduzir/remover itens.
  if (delta > 0 && quantity > Math.min(30, product.stock)) return toast('Limite de quantidade ou estoque atingido.');
  if (quantity <= 0) delete cart[id]; else cart[id] = quantity;
  pendingKey = null;
  persist(); renderCart();
});
$('#open-cart').onclick = () => { showCart(); openDialog(); };
$('#close-cart').onclick = () => $('#cart-dialog').close();
$('#last-order').onclick = async () => {
  if (busy) return;
  const button = $('#last-order');
  button.disabled = true;
  try {
    const order = await loadLatestOrder();
    if (!order) return toast('Não há pedido disponível nesta sessão.');
    showReceipt(order); openDialog();
  } catch (error) { toast(error.message || 'Falha de conexão. Tente novamente.'); }
  finally { button.disabled = false; }
};
$('#checkout').onsubmit = async event => {
  event.preventDefault();
  if (busy) return;
  if (!validatePhone()) { phoneField.reportValidity(); return; }
  busy = true; renderCart();
  $('#checkout-error').textContent = '';
  try {
    pendingKey = pendingKey || crypto.randomUUID();
    persist();
    const fields = new FormData(event.target);
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Shop-Request': 'checkout' },
      body: JSON.stringify({ name: fields.get('name'), phone: fields.get('phone'), cart, key: pendingKey })
    });
    const order = await response.json();
    if (!response.ok) throw Error(order.error || 'Não foi possível registrar seu pedido.');
    cart = {}; pendingKey = null;
    persist();
    $('#checkout').reset(); phoneField.setCustomValidity('');
    showReceipt(order);
    try { await load(); }
    catch { toast('Pedido registrado. Atualize a vitrine para ver o estoque.'); }
  } catch (error) {
    $('#checkout-error').textContent = error.message || 'Falha de conexão. Tente novamente.';
  } finally { busy = false; renderCart(); }
};
load().catch(error => { $('#products').textContent = ''; $('#catalog-error').textContent = error.message; });
loadLatestOrder().catch(() => {
  // Mantém a opção disponível para repetir uma consulta que falhou por rede.
  $('#last-order').hidden = false;
});
