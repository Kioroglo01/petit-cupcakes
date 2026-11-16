"""Entrada da aplicação. Python 3.10+, sem dependências externas."""
import os, argparse
from pathlib import Path
from http.server import ThreadingHTTPServer
from controllers.shop import ShopController
from models.store import Store

def create_server(host='127.0.0.1',port=8000,db_path=None):
 root=Path(__file__).resolve().parent
 server=ThreadingHTTPServer((host,port),ShopController)
 server.root=root; server.secure=os.getenv('COOKIE_SECURE')=='1'
 server.store=Store(db_path or os.getenv('DATABASE_PATH',str(root/'shop.sqlite3')))
 return server
if __name__=='__main__':
 parser=argparse.ArgumentParser(description='Loja Petit')
 parser.add_argument('--host',default=os.getenv('HOST','127.0.0.1'))
 parser.add_argument('--port',type=int,default=int(os.getenv('PORT','8000')))
 parser.add_argument('--strictPort',action='store_true',help=argparse.SUPPRESS)
 args=parser.parse_args()
 server=create_server(args.host,args.port)
 print(f'Abra http://localhost:{server.server_port} — Ctrl+C para encerrar')
 try: server.serve_forever()
 except KeyboardInterrupt: pass
 finally: server.server_close()
