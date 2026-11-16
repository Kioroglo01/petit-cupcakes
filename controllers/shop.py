from http.server import BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from urllib.parse import urlsplit
import json, secrets, mimetypes, logging

class ShopController(BaseHTTPRequestHandler):
 def log_message(self,fmt,*args): pass
 def respond(self,status,data,kind='application/json; charset=utf-8'):
  body=json.dumps(data,ensure_ascii=False).encode() if isinstance(data,(dict,list)) else data
  self.send_response(status)
  self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body)))
  self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Cache-Control','no-store')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
  if getattr(self,'new_session',False): self.send_header('Set-Cookie',f'shop={self.sid}; HttpOnly; SameSite=Strict; Path=/; Max-Age=604800'+('; Secure' if self.server.secure else ''))
  self.end_headers(); self.wfile.write(body)
 def session(self):
  cookie=SimpleCookie()
  try: cookie.load(self.headers.get('Cookie',''))
  except Exception: pass
  self.sid=cookie['shop'].value if 'shop' in cookie else ''
  if not self.sid or len(self.sid)!=43:
   self.sid=secrets.token_urlsafe(32); self.new_session=True
 def do_GET(self):
  self.session(); path=urlsplit(self.path).path
  if path=='/api/products': return self.respond(200,self.server.store.products())
  if path.startswith('/api/orders/'):
   order=self.server.store.order(path.rsplit('/',1)[1],self.sid)
   return self.respond(200,order) if order else self.respond(404,{'error':'Pedido não encontrado nesta sessão.'})
  if path=='/': file=self.server.root/'views/index.html'
  elif path in ('/static/app.js','/static/style.css'): file=self.server.root/path[1:]
  else: return self.respond(404,{'error':'Página não encontrada.'})
  self.respond(200,file.read_bytes(),mimetypes.guess_type(str(file))[0]+'; charset=utf-8')
 def do_POST(self):
  self.session()
  if urlsplit(self.path).path!='/api/orders': return self.respond(404,{'error':'Rota não encontrada.'})
  if self.headers.get('X-Shop-Request')!='checkout': return self.respond(403,{'error':'Requisição não autorizada.'})
  if self.headers.get('Content-Type','').split(';')[0]!='application/json': return self.respond(415,{'error':'Envie JSON.'})
  try:
   size=int(self.headers.get('Content-Length','0'))
   if not 0<size<=16000: return self.respond(413,{'error':'Requisição muito grande ou vazia.'})
   data=json.loads(self.rfile.read(size))
   self.respond(201,self.server.store.checkout(self.sid,data))
  except (ValueError,UnicodeDecodeError):
   import sys
   error=sys.exc_info()[1]
   message=str(error) if type(error) is ValueError else 'JSON inválido.'
   self.respond(400,{'error':message})
  except Exception:
   logging.exception('Falha no checkout'); self.respond(500,{'error':'Não foi possível concluir. Tente novamente com o mesmo carrinho.'})
