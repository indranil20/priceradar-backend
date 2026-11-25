import os,re
from urllib.parse import urlparse,unquote
import requests
from flask import Flask,render_template,request,jsonify
from dotenv import load_dotenv
load_dotenv()
app=Flask(__name__)
@app.get('/')
def home(): return render_template('index.html')
@app.post('/api/compare')
def compare():
    data=request.get_json(silent=True) or {}; q=str(data.get('query','')).strip()[:500]
    if not q:return jsonify(error='Enter a product name or URL.'),400
    if q.startswith(('https://','http://')):
        u=urlparse(q); parts=unquote(u.path).split('/'); candidates=[p for p in parts if p.count('-')>=2 and len(p)>15]
        if not candidates:return jsonify(error='This URL does not contain a readable product name. Enter the exact model and variant instead.'),400
        q=max(candidates,key=len).replace('-',' ')
    key=os.getenv('SERPAPI_KEY')
    if not key:return jsonify(error='Configure SERPAPI_KEY in the server .env file to enable live search.'),503
    try:
        r=requests.get('https://serpapi.com/search.json',params={'engine':'google_shopping','q':q,'gl':'in','hl':'en','api_key':key},timeout=25); r.raise_for_status(); payload=r.json()
        if payload.get('error'):return jsonify(error='Shopping provider returned an error. Check API configuration and quota.'),502
    except (requests.RequestException,ValueError):return jsonify(error='Shopping provider unavailable. Try again later.'),502
    offers=[]
    for x in payload.get('shopping_results',[]):
        price=x.get('extracted_price'); label=x.get('price','')
        if not isinstance(price,(int,float)) or price<=0 or '₹' not in label:continue
        link=x.get('product_link') or x.get('link') or ''
        if not link.startswith('https://'):link=''
        offers.append({'title':x.get('title',''),'store':x.get('source','Unknown seller'),'price':price,'link':link,'delivery':x.get('delivery','Not verified')})
    return jsonify(query=q,offers=sorted(offers,key=lambda x:x['price']))
if __name__=='__main__':app.run(port=5000)
