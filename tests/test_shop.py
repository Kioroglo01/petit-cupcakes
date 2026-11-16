import unittest,tempfile,threading,json,urllib.request,urllib.error,http.cookiejar,sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from app import create_server
from models.store import Store

class ModelTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.path=str(Path(self.tmp.name)/'test.db'); self.store=Store(self.path)
 def tearDown(self): self.tmp.cleanup()
 def data(self,**kw): return dict(name='Ana Silva',phone='11999999999',key='a'*32,cart={'1':2},**kw)
 def test_price_stock_and_persistence(self):
  order=self.store.checkout('owner',self.data());self.assertEqual(order['total'],2800)
  self.assertEqual(Store(self.path).products()[0]['stock'],38)
  self.assertEqual(Store(self.path).order(order['token'],'owner')['total'],2800)
 def test_retry_does_not_duplicate(self):
  first=self.store.checkout('owner',self.data());second=self.store.checkout('owner',self.data())
  self.assertEqual(first['token'],second['token']);self.assertEqual(self.store.products()[0]['stock'],38)
 def test_order_is_private(self):
  o=self.store.checkout('owner',self.data());self.assertIsNone(self.store.order(o['token'],'other'))
 def test_invalid_inputs(self):
  for field,value in [('cart',{}),('cart',{'1':-1}),('cart',{'1':True}),('cart',{'1':1.5}),('cart',{'999':1}),('name',''),('phone','123'),('key','short')]:
   data=self.data();data[field]=value
   with self.subTest(field=field,value=value),self.assertRaises(ValueError):self.store.checkout('owner',data)
 def test_atomic_rollback(self):
  data=self.data();data['cart']={'1':2,'999':1}
  with self.assertRaises(ValueError):self.store.checkout('owner',data)
  self.assertEqual(self.store.products()[0]['stock'],40)
 def test_concurrent_stock(self):
  def buy(i):
   data=self.data();data['key']=str(i)*32;data['cart']={'1':30}
   try:self.store.checkout(str(i),data);return True
   except ValueError:return False
  with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(buy,[1,2]))
  self.assertEqual(sum(result),1);self.assertEqual(self.store.products()[0]['stock'],10)

 def test_phone_rejects_letters_and_invalid_formats(self):
  for phone in ['11999999999abc','abc11999999999','00000000000','(11 99999-9999','11) 99999-9999','+55 11 99999-9999','１１９９９９９９９９９']:
   data=self.data();data['phone']=phone
   with self.subTest(phone=phone),self.assertRaises(ValueError):self.store.checkout('owner',data)
  self.assertEqual(self.store.products()[0]['stock'],40)
 def test_phone_accepts_and_normalizes_valid_formats(self):
  for index,phone in enumerate(['11999999999','(11) 99999-9999','11 99999-9999','(11) 3333-4444']):
   data=self.data();data['phone']=phone;data['key']=str(index)*32
   self.store.checkout('owner',data)
  with self.store.db() as db:
   self.assertEqual(db.execute('SELECT phone FROM orders ORDER BY rowid DESC LIMIT 1').fetchone()['phone'],'1133334444')
 def test_latest_order_survives_restart_and_is_private(self):
  self.assertIsNone(self.store.latest_order('owner'))
  first=self.store.checkout('owner',self.data())
  data=self.data();data['key']='b'*32
  second=self.store.checkout('owner',data)
  reopened=Store(self.path)
  self.assertEqual(reopened.latest_order('owner')['token'],second['token'])
  self.assertNotEqual(first['token'],second['token'])
  self.assertIsNone(reopened.latest_order('other'))

class HTTPTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.server=create_server(port=0,db_path=str(Path(self.tmp.name)/'test.db'))
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
  self.base=f'http://127.0.0.1:{self.server.server_port}';self.client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def get(self,path):return self.client.open(self.base+path)
 def test_frontend_assets(self):
  for path,needle in [('/',b'petit'),('/static/style.css',b'@media'),('/static/app.js',b'/api/orders')]:
   with self.get(path) as r:self.assertEqual(r.status,200);self.assertIn(needle,r.read())
 def test_local_cupcake_images(self):
  names=['red-velvet','chocolate-intenso','morango-dos-sonhos','limao-siciliano','doce-de-leite','baunilha-confete']
  for name in names:
   with self.subTest(flavor=name),self.get('/static/images/'+name+'.png') as r:
    self.assertEqual(r.status,200)
    self.assertEqual(r.headers['Content-Type'],'image/png')
    self.assertTrue(r.read().startswith(b'\x89PNG\r\n\x1a\n'))
    self.assertNotIn('https:',r.headers['Content-Security-Policy'])
  for path in ['/static/images/../../app.py','/static/images/%2e%2e/app.py','/static/images/missing.png']:
   with self.subTest(path=path),self.assertRaises(urllib.error.HTTPError) as err:self.get(path)
   self.assertEqual(err.exception.code,404)
 def test_full_checkout_and_lookup(self):
  products=json.load(self.get('/api/products'));self.assertEqual(len(products),6)
  data={'name':'Ana Silva','phone':'11999999999','key':'z'*32,'cart':{'1':2},'total':1}
  req=urllib.request.Request(self.base+'/api/orders',json.dumps(data).encode(),{'Content-Type':'application/json','X-Shop-Request':'checkout'})
  with self.client.open(req) as r:self.assertEqual(r.status,201);order=json.load(r)
  self.assertEqual(order['total'],2800)
  self.assertEqual(json.load(self.get('/api/orders/'+order['token']))['total'],2800)
  with self.assertRaises(urllib.error.HTTPError) as err:urllib.request.urlopen(self.base+'/api/orders/'+order['token'])
  self.assertEqual(err.exception.code,404)
 def test_latest_order_api_and_session_isolation(self):
  self.assertIsNone(json.load(self.get('/api/orders/latest'))['order'])
  data={'name':'Cliente teste','phone':'(11) 99999-9999','key':'c'*32,'cart':{'1':1}}
  req=urllib.request.Request(self.base+'/api/orders',json.dumps(data).encode(),{'Content-Type':'application/json','X-Shop-Request':'checkout'})
  order=json.load(self.client.open(req))
  self.assertEqual(json.load(self.get('/api/orders/latest'))['order']['token'],order['token'])
  self.assertIsNone(json.load(urllib.request.urlopen(self.base+'/api/orders/latest'))['order'])
 def test_checkout_rejects_phone_with_letters(self):
  data={'name':'Cliente teste','phone':'11999999999abc','key':'d'*32,'cart':{'1':1}}
  req=urllib.request.Request(self.base+'/api/orders',json.dumps(data).encode(),{'Content-Type':'application/json','X-Shop-Request':'checkout'})
  with self.assertRaises(urllib.error.HTTPError) as err:self.client.open(req)
  self.assertEqual(err.exception.code,400)
  self.assertIn('sem letras',json.load(err.exception)['error'])
  self.assertEqual(self.server.store.products()[0]['stock'],40)
 def test_errors(self):
  for path,payload,headers,status in [('/api/orders',b'{}',{'Content-Type':'application/json'},403),('/api/orders',b'{',{'Content-Type':'application/json','X-Shop-Request':'checkout'},400),('/api/orders',b'{}',{'Content-Type':'text/plain','X-Shop-Request':'checkout'},415),('/invalid',b'{}',{},404)]:
   req=urllib.request.Request(self.base+path,payload,headers)
   with self.subTest(status=status),self.assertRaises(urllib.error.HTTPError) as err:self.client.open(req)
   self.assertEqual(err.exception.code,status)
 def test_no_file_traversal(self):
  with self.assertRaises(urllib.error.HTTPError) as err:self.get('/static/../app.py')
  self.assertEqual(err.exception.code,404)
if __name__=='__main__':unittest.main()
