import sqlite3, secrets, json, re
from contextlib import contextmanager

PRODUCTS = [
 ('Red velvet','Clássicos','Massa aveludada de cacau e cobertura de cream cheese.',1400,'#bd4d60','#fff1e1'),
 ('Chocolate intenso','Clássicos','Chocolate na massa, no recheio e no seu melhor momento.',1300,'#64372e','#a46c51'),
 ('Morango dos sonhos','Frutados','Massa de baunilha, geleia de morango e creme delicado.',1500,'#df8da6','#ffe2d8'),
 ('Limão siciliano','Frutados','O encontro do creme de limão com um merengue leve.',1400,'#d9c35e','#fff6c6'),
 ('Doce de leite','Clássicos','Massa fofinha com recheio cremoso de doce de leite.',1500,'#b57649','#f4cf9e'),
 ('Baunilha & confete','Especiais','Baunilha de verdade e uma pequena festa em cada mordida.',1200,'#b18ac3','#f4dcf7')]

class Store:
 def __init__(self, path):
  self.path = path
  with self.db() as db:
   db.executescript('''CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT,category TEXT,description TEXT,price INTEGER CHECK(price>0),color TEXT,cream TEXT,stock INTEGER CHECK(stock>=0));
CREATE TABLE IF NOT EXISTS orders(token TEXT PRIMARY KEY,owner TEXT NOT NULL,request_key TEXT NOT NULL,customer TEXT,phone TEXT,total INTEGER,items TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(owner,request_key));''')
   if not db.execute('SELECT 1 FROM products').fetchone():
    db.executemany('INSERT INTO products(name,category,description,price,color,cream,stock) VALUES(?,?,?,?,?,?,40)',PRODUCTS)
 @contextmanager
 def db(self):
  db=sqlite3.connect(self.path,timeout=10); db.row_factory=sqlite3.Row
  try:
   yield db; db.commit()
  except Exception:
   db.rollback(); raise
  finally: db.close()
 def products(self):
  with self.db() as db: return [dict(r) for r in db.execute('SELECT * FROM products')]
 def checkout(self,owner,data):
  if not isinstance(data,dict): raise ValueError('Dados inválidos.')
  name=data.get('name',''); phone=data.get('phone',''); key=data.get('key',''); cart=data.get('cart',{})
  if not isinstance(name,str) or not 2<=len(name.strip())<=100: raise ValueError('Informe seu nome (2 a 100 caracteres).')
  if not isinstance(phone,str) or not re.fullmatch(r'(?:\([1-9][0-9]\)|[1-9][0-9]) ?(?:9[0-9]{4}|[2-5][0-9]{3})-?[0-9]{4}',phone.strip()):
   raise ValueError('Informe um telefone válido com DDD, sem letras. Ex.: (11) 99999-9999.')
  phone=re.sub(r'[^0-9]','',phone)
  if not isinstance(key,str) or not 16<=len(key)<=100: raise ValueError('Identificador de compra inválido.')
  if not isinstance(cart,dict) or not 1<=len(cart)<=30: raise ValueError('Seu carrinho está vazio ou inválido.')
  with self.db() as db:
   db.execute('BEGIN IMMEDIATE')
   existing=db.execute('SELECT token FROM orders WHERE owner=? AND request_key=?',(owner,key)).fetchone()
   if existing: return self.order(existing['token'],owner)
   items=[]; total=0
   for pid,qty in cart.items():
    if not isinstance(pid,str) or not pid.isdigit() or type(qty) is not int or not 1<=qty<=30: raise ValueError('Quantidade inválida: escolha de 1 a 30 por sabor.')
    p=db.execute('SELECT * FROM products WHERE id=?',(int(pid),)).fetchone()
    if not p: raise ValueError('Produto não encontrado.')
    if qty>p['stock']: raise ValueError(f'Estoque insuficiente para {p["name"]}.')
    total+=p['price']*qty
    items.append({'name':p['name'],'quantity':qty,'price':p['price']})
    db.execute('UPDATE products SET stock=stock-? WHERE id=?',(qty,p['id']))
   token=secrets.token_urlsafe(24)
   db.execute('INSERT INTO orders(token,owner,request_key,customer,phone,total,items) VALUES(?,?,?,?,?,?,?)',(token,owner,key,name.strip(),phone,total,json.dumps(items)))
  return self.order(token,owner)
 def order(self,token,owner):
  with self.db() as db:
   row=db.execute('SELECT token,customer,total,items,created FROM orders WHERE token=? AND owner=?',(token,owner)).fetchone()
   if not row: return None
   result=dict(row); result['items']=json.loads(result['items']); result['status']='Recebido · pagamento na retirada'; return result

 def latest_order(self,owner):
  with self.db() as db:
   row=db.execute('SELECT token FROM orders WHERE owner=? ORDER BY rowid DESC LIMIT 1',(owner,)).fetchone()
  return self.order(row['token'],owner) if row else None
