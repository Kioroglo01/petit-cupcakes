// Regressões do comportamento do cliente, executadas sem bibliotecas externas.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
const order = {token:'test-order-token',customer:'Cliente teste',total:1400,status:'Recebido',items:[{name:'Red velvet',quantity:1,price:1400}]};
const product = {id:1,name:'Red velvet',category:'Clássicos',description:'Teste',stock:40,price:1400,color:'#bd4d60',cream:'#fff1e1'};
async function setup({latest=null,stock=40,saved={}}={}) {
  const elements = new Map(), requests = [], storage = new Map(Object.entries(saved));
  const get = selector => {
    if (!elements.has(selector)) elements.set(selector, {
      hidden:false,disabled:false,open:false,textContent:'',innerHTML:'',value:'',validity:'',
      classList:{add(){},remove(){},toggle(){}},listeners:{},
      addEventListener(type,fn){this.listeners[type]=fn},
      setCustomValidity(message){this.validity=message},reportValidity(){this.reported=true},
      showModal(){this.open=true},close(){this.open=false},reset(){}
    });
    return elements.get(selector);
  };
  const context=vm.createContext({
    document:{querySelector:get,querySelectorAll:()=>[]},Intl,console,
    localStorage:{getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v),removeItem:k=>storage.delete(k)},
    setTimeout:()=>0,crypto:{randomUUID:()=> 'request-key-for-regression'},
    FormData:class {get(key){return key==='phone'?get('#checkout input[name="phone"]').value:'Cliente teste'}},
    fetch:async(url,options)=>{
      requests.push({url,options});
      let data;
      if(url==='/api/products')data=[{...product,stock}];
      else if(url==='/api/orders/latest')data={order:latest};
      else data=order;
      return {ok:true,json:async()=>data};
    }
  });
  vm.runInContext(source,context);
  await new Promise(setImmediate);
  return {get,requests,context};
}
function clickProduct(app) {
  app.get('#products').listeners.click({target:{closest:()=>({dataset:{add:'1'}})}});
}
test('telefone com letras impede POST de checkout',async()=>{
  const app=await setup();clickProduct(app);
  app.get('#checkout input[name="phone"]').value='11999999999abc';
  await app.get('#checkout').onsubmit({preventDefault(){},target:{}});
  assert.equal(app.requests.filter(r=>r.options?.method==='POST').length,0);
  assert.match(app.get('#checkout input[name="phone"]').validity,/sem letras/);
});
test('nova compra mostra carrinho depois de confirmação anterior',async()=>{
  const app=await setup();clickProduct(app);
  app.get('#checkout input[name="phone"]').value='(11) 99999-9999';
  await app.get('#checkout').onsubmit({preventDefault(){},target:{}});
  assert.equal(app.get('#receipt').hidden,false);
  assert.equal(app.get('#checkout').hidden,true);
  clickProduct(app);app.get('#open-cart').onclick();
  assert.equal(app.get('#receipt').hidden,true);
  assert.equal(app.get('#checkout').hidden,false);
  assert.equal(app.get('#cart-items').hidden,false);
  assert.equal(app.get('#count').textContent,1);
});
test('após recarga recupera último pedido do servidor e mantém sacola',async()=>{
  const app=await setup({latest:order,saved:{'petit-cart':'{"1":2}'}});
  assert.equal(app.get('#last-order').hidden,false);
  await app.get('#last-order').onclick();
  assert.match(app.get('#receipt').innerHTML,/test-order-token/);
  assert.match(app.get('#receipt').innerHTML,/Red velvet/);
  app.get('#new-order').onclick();
  assert.equal(app.get('#checkout').hidden,false);
  assert.equal(app.get('#count').textContent,2);
});
test('sessão sem pedidos oculta botão de último pedido',async()=>{
  const app=await setup();assert.equal(app.get('#last-order').hidden,true);
});
test('estoque reduzido não impede diminuir quantidade antiga na sacola',async()=>{
  const app=await setup({stock:1,saved:{'petit-cart':'{"1":5}'}});
  app.get('#cart-items').listeners.click({target:{closest:()=>({dataset:{change:'1',delta:'-1'}})}});
  assert.equal(app.get('#count').textContent,4);
});
