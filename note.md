# TODO
- gestion erreur
https://github.com/zilliztech/attu?tab=readme-ov-file#install-desktop-application
- connect fastapi&batch and n8n
  - ip route | grep default
gnome-terminal -- bash -c "/vagrant/mapreducesurvey/./run_surveys_pipeline.sh; exec bash"

Très fiable : score ≥ 0.85–0.90
Pertinent : score ≥ 0.70–0.80
Brouillard : score < 0.65

Tronquage simple (max_messages) : évite de dépasser la fenêtre contextuelle. Tu peux plus tard remplacer par un tronquage token-based ou par des résumés des vieux tours. X

Détection de langue locale (gratuite) X

Traduction → FR uniquement si la langue dominante est le malagasy (pour l’embedding / recherche) X

Réponse dans la langue de l’utilisateur (le LLM répond dans la langue détectée) X

tronquage historique et input_token X

candidate_count: nombre de réponses que le modèle génère en parallèle pour une même requête.
temperature: C’est un curseur d’exploration. Le modèle calcule des probabilités pour le prochain mot ; la temperature étire ou resserre ces probabilités avant de choisir.
limit input token, cote front

---

2025-09-27 01:08:29,078 - app.services.milvus_service - WARNING - Insertion de 1026 chunks dans Milvus.   
2025-09-27 01:09:13,902 [ERROR][handler]: RPC error: [upsert_rows], <MilvusException: (code=1100, message=length of varchar field content exceeds max length, row number: 18, length: 10046, max length: 10000: invalid parameter)>, <Time:{'RPC start': '2025-09-27 01:08:29.078673', 'RPC error': '2025-09-27 01:09:13.902074'}> (decorators.py:140)
2025-09-27 01:09:14,030 - app.api.v1.routes - WARNING - Traceback (most recent call last):
  File "D:\2M\assistant\full\app\app\api\v1\routes.py", line 164, in update_documents_milvus
    message = MilvusService().bulk_insert_documents_to_milvus()

## close running port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object LocalAddress,LocalPort,State,OwningProcess
 
Get-Process -Id  19316 <PID>
Stop-Process -Id  12756 -Force

## python
python -m venv venv
venv\Scripts\activate

uvicorn
borneo
aiofiles

pip install fastapi uvicorn 
pip install -r requirements.txt
pip install python-dotenv
pip install pydantic-settings
pip install transformers
pip install tiktoken
  léger, rapide, open-source et très proche des tokenizers utilisés par la plupart des LLMs modernes.
  pip install google-cloud-translate==3.* python-dotenv
pip install httpx PyJWT python-multipart
pip install google-cloud-aiplatform 
pip install langdetect (dfidn t work)
pip install fasttext-wheel pycld3 (didn't work)
  D:\2M\assistant\aiAgentTesting\venv\Scripts\python.exe -m pip install --upgrade pip
  download fasttext-0.9.2-cp311-cp311-win_amd64.whl in https://github.com/mdrehan4all/fasttext_wheels_for_windows/blob/main/fasttext-0.9.2-cp311-cp311-win_amd64.whl (turn out that it will only works on python 3.11 not 3.13)
  download lid.176.ftz
  pip install C:\Users\Kaloina\Downloads\fasttext-0.9.2-cp311-cp311-win_amd64.whl
or 
pip install langid
pip install motor==3.6.0
pip install pytest==8.3.2
pip install pytest-asyncio==0.23.8
pip install asgi-lifespan==2.1.0
pip install pydantic[email]

pip freeze > requirement.txt

-- tsy nety
pip install oraclenosqldb 
pip install --upgrade google-genai


pip install aiofiles
pip install pyhive
pip install thrift
pip install sasl XX
pip install thrift_sasl XX
pip install pymilvus==2.5.3

-- comme oraclenosqldb didn't work
pip install borneo

if oracle cloud infrastructure
pip install oci

pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
scikit-learn>=1.3.0
requests>=2.31.0
umap-learn>=0.5.5

['04258211665b474dbe6fd9107fba52d6', '0499721d290044369e8b6c62ddbbf1d5', '2ab6afd85a674aee8d9399fdd5835774']

## milvus cluster
user
db_119f456d635d533
mdp
Yh2;,^NJDYelm9-L

api key
bba8be7aea9c31484c69c4022a003e301de1002dc1e6dbed02aab0715cb2f830d84145456603e365e62320f880e0557defa83332

uri = https://in03-119f456d635d533.serverless.aws-eu-central-1.cloud.zilliz.com
token = bba8be7aea9c31484c69c4022a003e301de1002dc1e6dbed02aab0715cb2f830d84145456603e365e62320f880e0557defa83332

curl --request POST \
  --url https://in03-119f456d635d533.serverless.aws-eu-central-1.cloud.zilliz.com/v2/vectordb/collections/list \
  --header 'accept: application/json' \
  --header 'authorization: Bearer bba8be7aea9c31484c69c4022a003e301de1002dc1e6dbed02aab0715cb2f830d84145456603e365e62320f880e0557defa83332' \
  --data '{}'
  

## run server
cd full/app/app
venv\Scripts\activate
cd ../
uvicorn app.main:app --reload

timer
charNoSpace 8587 charSpace 10215  embed   11s 

python -m pip show <nom_paquet>
python -m pip list

python -m pip uninstall <nom_paquet>
python -m pip uninstall -y <nom_paquet>

## embedding gemini
https://cloud.google.com/vertex-ai/generative-ai/docs/embeddings/get-text-embeddings?hl=fr

jeu d’or simulé” ou “jeu de test MGMERL synthétique”.
Transformer tout ça en Notebook d’évaluation (UMAP, histos cosines, tableaux CSV) prêt à exécuter,
Ou créer des endpoints FastAPI /eval/run et /eval/plots comme prévu.

Étape 2 : calcul des premières métriques de recherche (Recall@k, Precision@k, nDCG, MRR) mxbai vs Gemini, + tableaux et graphiques exportables pour ta soutenance.

sortie:
per_query_metrics
aggregate_metrics
charts image:
R@10_by_model
nDCG@10_by_model
MRR_by_model
P@10_by_model

qrels = la vérité terrain pour calculer Recall@k / nDCG / MRR (évaluation IR robuste).

hard_negative_ids = indispensable pour séparer un bon embedding d’un médiocre sur des cas ambigus.


python eval_ir.py --data-dir D:/2M/assistant/full/app/app/eval/data --out-dir outputs/mxbai_search --mode runs --runs-csv D:/2M/assistant/full/app/app/eval/data/runs_mxbai_search.csv
python eval_ir.py --data-dir D:/2M/assistant/full/app/app/eval/data --out-dir outputs/gemini_search --mode runs --runs-csv D:/2M/assistant/full/app/app/eval/data/runs_gemini_search.csv

python eval_ir.py --data-dir D:/2M/assistant/full/app/app/eval/data --out-dir outputs/mxbai_formation --mode runs --runs-csv D:/2M/assistant/full/app/app/eval/data/runs_mxbai_formation.csv
python eval_ir.py --data-dir D:/2M/assistant/full/app/app/eval/data --out-dir outputs/gemini_formation --mode runs --runs-csv D:/2M/assistant/full/app/app/eval/data/runs_gemini_formation.csv


python combine_and_compare.py  --runs outputs/mxbai_search/aggregate_metrics.csv outputs/gemini_search/aggregate_metrics.csv  --per-query outputs/mxbai_search/per_query_metrics.csv outputs/gemini_search/per_query_metrics.csv  --out-dir outputs/compare_search

python combine_and_compare.py --runs outputs/mxbai_formation/aggregate_metrics.csv outputs/gemini_formation/aggregate_metrics.csv --per-query outputs/mxbai_formation/per_query_metrics.csv outputs/gemini_formation/per_query_metrics.csv --out-dir outputs/compare_formation

python eval_intrinsic.py --emb-csv D:/2M/assistant/full/app/app/eval/data/embeddings_mxbai.csv --out-dir outputs/intrinsic_mxbai

python eval_intrinsic.py --emb-csv D:/2M/assistant/full/app/app/eval/data/embeddings_gemini.csv --out-dir outputs/intrinsic_gemini --umap 1



## mongo
mongosh "mongodb+srv://melodiekaloina_db_user:GiZE2WEocgH988cM@cluster0.82og86s.mongodb.net/"
use chatdb
db.conversations.getIndexes()
db.messages.getIndexes()
db.conversations.deleteOne({"title"= "Conversation à 00:20 16/09/2025"})
db.messages.deleteMany({})


## oracle nosql
- add this in vagrantfile
config.vm.network "forwarded_port", guest: 5000, host: 5000
then
vagrant reload
connect store -name kvstore -host 0.0.0.0 -port 5000;

nohup java -Xmx64m -Xms64m -jar $KVHOME/lib/kvstore.jar kvlite -secure-config disable -root $KVROOT &

//Demarrage du client ligne de commandes Oracle NOSQL
[vagrant@oracle-21c-vagrant ~]$ java -jar $KVHOME/lib/kvstore.jar runadmin -port 5000 -host localhost


nohup java -Xmx64m -Xms64m -jar $KVHOME/lib/kvstore.jar kvlite -secure-config disable -store kvstore -root $KVROOT -port 5000 -host localhost &

execute 'DROP TABLE test';
execute 'CREATE TABLE test (id INTEGER GENERATED ALWAYS AS IDENTITY, name STRING, PRIMARY KEY(id))';

## milvus
milvus.io/docs/fr/v2.5.x/single-vector-search.md#Enchancing-ANN-Search

http://10.174.27.253:9091/webui/collections

curl http://192.168.47.253:11434/api/embed -d '{"model": "mxbai-embed-large","keep_alive":-1, "input": "test"}' 
curl https://ollama.34.46.81.46.nip.io/api/embed -d '{"model": "mxbai-embed-large","keep_alive":-1, "input": "test"}' 
curl http://192.168.47.253:11434/api/generate -d '{"model": "llama3.2","keep_alive":-1, "prompt": "Bonjour"}'

curl http://192.168.47.253:11434/api/tags
curl http://192.168.47.253:11434/api/show -d '{"name": "mxbai-embed-large"}'

curl http://192.168.47.253:11434/api/pull -d '{"name": "mxbai-embed-large"}'

## teste proxy et vrai kvstore

java -jar $KVHOME/lib/httpproxy.jar \
  -storeName kvstore \
  -helperHosts localhost:5000 \
  -httpPort 8080 \
  -verbose true

nohup java -jar $KVHOME/lib/kvstore.jar start -root /var/kv &

java -jar $KVHOME/lib/kvstore.jar makebootconfig \
  -root /var/kv \
  -store kvstore \
  -host localhost \
  -port 5000 \
  -harange 5110,5120 \
-admin-web-port 5200
  -force


 echo $KVROOT
/var/kv


ps aux | grep kvstore

sudo ss -lptn 'sport = :5000'
sudo kill -9  9228 <PID>

C:/Users/Kaloina/.vagrant.d/data/machine-index/index

1521
5500
10000
10002
8888
5000
8080

c pas sur si c'est le command
Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess

tasklist /FI "PID eq <PID>"

Stop-Process -Id  3584 -Force

tasklist | findstr python
python.exe                   15052 Console                    1    118,976 K
python.exe                    7444 Console                    1    244,284 K
Stop-Process -Name python -Force

## login
j'ai api de vrai login de mwater en tant que user
https://api.mwater.co/v3/clients
avec body
{
    "username":"melodiekaloina@gmail.com",
    "password": password brute
}
et retourne un element json comme ceci, avec tous les groups ou l'user y sont
{
  "client": "a7937ed3ff78f4f68997f5df7b3e2c76",
  "email": "melodiekaloina@gmail.com",
  "user": "4e51c07bb112475db749a56932afc2de",
  "username": "Kaloina Ravoahangilalao",
  "createdAt": "2024-12-19T05:43:09.801Z",
  "givenName": "Kaloina",
  "familyName": "Ravoahangilalao",
  "groups": [
    "007f4c58663f49cf9070cc352dbf99ae",
    "0105e57096ea4399b70e9868fb8d5896",
    "0131dae42ea54930b031ef0983ce7747",
    "019605851fe44db1a608131b5c3720a5",
    "01a0fd1f534a43548f0a0ea844af5c13",
    "02ab6428eda744f9b3d7e415804d683a",
    "0380e837010f4806b20286c2fe9aa282",
    "038ba09e99ce48aaadc5d159712268ba",
    "03d4394b387f4a0280db826c94bdc73c",
    "0407ef502529404187efb2025b639c54",
    "0473af103aa74fea9db64d9689a13b0f",
    "0495576c5dd14d8fb08279ae350d5a02",
    "049e2880fdfb4bac8226ac1c6b5abda9",
    "05b4cb8056c844e49ceaa820150bc464",
    "05e8b53bfa514c88805930d34f1e5201",
    "062f7b9a8bf044e7bf9b7823b07da85d",
    "063108a355044e19b98aa01b55643a04",
    "064caba944c447d9af8e60e22b62edac",
    "0696dc98a9ad4ee7aae7bf1a95d493af",
    "06de78d6bc724c3d82f899affaf298bd",
    "08361b122b5f4881b7dbf623704ed58a",
    "0981cdf9d039488aa97ae29c17c707da",
    "09f1899d9d81436b8aa5f11def59659e",
    "0a08cecc2f7f4a72ac6ab23443fe1e3b",
    "0a2edae11d9843c39f2b32959b2a1f4c",    
    "ffe39ffaa7d946e5826993e145029b2f"
  ],
  "emailConfirmed": true,
  "ageConfirmed": true
}

et retourne 403 si erreur avec
{
  "error": "Sorry, that username, email, or password didn't work"
}

mais je veur gerer de tel sorte que j'ai aussi le liste d'user qui sont admin, dont soit email ou username sont stocker quelque part dans mon cote (a reflechir ou dans le datalake, peut etre mysql mais pour le moment faisont simple sans base de donnee), donc le service login dans mon fastapi sera, l'utilisateur se connecte avec son compte officiel et si login officiel success, on retourne le meme objet json contenant tous les informations, mais avec l'information on doit indiquer si c'est un admin ou pas pour que coter front je peux gerer le droit d'acces de quelque lien, mais il faut que ca soit securiser pour que l'utilisateur ne peux pas juste modifier dans localstorage qu il est admin (donc il faut trouver quelque solution pour cela, je n'ai aucune idee pour la securisation (cache client ?? je sais pas franchement)). Mais faisons etape par etape 

- Backend : authentifie chez mWater → signe un JWT (avec is_admin) → cookie HttpOnly.
- Frontend : lit is_admin depuis la réponse login puis, à chaque refresh, 1 appel /auth/me.
- UI : cache/affiche selon is_admin local.
- Sécurité vraie : toujours re-vérifiée côté backend via le cookie JWT.
- Moins d’appels : 1 au login, 1 à l’app start, puis plus rien (sauf API métier).
- En prod, ajoute Secure (HTTPS only).
- cookie HttpOnly + Secure + SameSite=Strict, TTL ~2h
- Tu es en cookie HttpOnly : pas besoin de donner access_token au JS (réduit la surface d’attaque).
- Empêcher le cache de la réponse de login.
- in set_session_cookie
  - Empêche lecture par JS (HttpOnly), force HTTPS (Secure en prod), bloque CSRF par défaut (SameSite=Strict), et optionnellement fixe le domain si front/back sont sur le même domaine racine.
- Limite les tentatives (in-memory simple pour démarrer).

- Stateless (JWT dans un cookie HttpOnly)
  - Cookie : contient tout (un JWT signé avec is_admin, sub, exp, …).
  - Serveur : ne garde rien en mémoire, il vérifie la signature à chaque requête.
  - Pros : simple à scaler, pas de store.
  - Cons : révocation immédiate plus compliquée (on compense par TTL court et, si besoin, une denylist temporaire).
  - HttpOnly = le JS ne peut pas lire le cookie → bien contre XSS (vol de token)
- Stateful (ID de session dans un cookie HttpOnly)
  - Cookie : contient un ID opaque.
  - Serveur : garde un store (ex: Redis) qui mappe session_id → {user, is_admin, …}.
  - Pros : tu peux révoquer/logout partout instantanément.
  - Cons : nécessite un store (complexité/maintenance).



Le document que j'ai consulté ne fournit pas une définition directe et complète du système MGMERL en tant que tel. Cependant, il décrit en détail un aspect fonctionnel lié à la plateforme "mWater Portal", qui est une composante ou un outil souvent associé à des systèmes de gestion de données.

Je n'ai pas trouvé un unique "Guide d'utilisation" général pour l'ensemble du système MGMERL. Cependant, les documents que j'ai à ma disposition sont des guides d'utilisation spécifiques, conçus pour différents rôles d'utilisateurs ou pour des processus particuliers au sein de la plateforme.

FORMATION, navigation
Si contenu vraiment inaccessible, genre vraiment pas de resultat, ben dans ce cas il faut que tu repond a partir de tes connaissances gemini, si dans tes connaissance tu trouve que la question n'a rien avoir avec systeme, ou suivi evaluation ou wash ben tu dis que rien avoir avec systeme mwater

FORMATION
Le resultat ne sont pas envoyer par l'utilisateur mais un processus du serveur, donc nne dit jamais que c'est l'utilisateur qui la donner. 


www-embed-player.js:1218 
 GET https://googleads.g.doubleclick.net/pagead/id net::ERR_BLOCKED_BY_CLIENT

Failed to load  googleads.g.doubleclick.net/pagead/id:1
resource: net::ERR_BLOCKED_BY_CLIENT

GET https://static.doubleclick.net/instream/ad_status.js net::ERR_BLOCKED_BY_CLIENT