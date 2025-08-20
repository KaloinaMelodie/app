# TODO
- gestion erreur
https://github.com/zilliztech/attu?tab=readme-ov-file#install-desktop-application
- connect fastapi&batch and n8n
  - ip route | grep default
gnome-terminal -- bash -c "/vagrant/mapreducesurvey/./run_surveys_pipeline.sh; exec bash"

## close running port 8000
Get-NetTCPConnection -LocalPort 8000 | Select-Object LocalAddress,LocalPort,State,OwningProcess

Get-Process -Id 19196 <PID>
Stop-Process -Id 19196 -Force

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


-- tsy nety
pip install oraclenosqldb 
pip install aiofiles
pip install pyhive
pip install thrift
pip install sasl 
pip install thrift_sasl


-- comme oraclenosqldb didn't work
pip install borneo

if oracle cloud infrastructure
pip install oci

['04258211665b474dbe6fd9107fba52d6', '0499721d290044369e8b6c62ddbbf1d5', '2ab6afd85a674aee8d9399fdd5835774']

## run server
venv\Scripts\activate
cd ../
uvicorn app.main:app --reload

timer
charNoSpace 8587 charSpace 10215  embed   11s


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
Get-NetTCPConnection -LocalPort 5000 -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess

tasklist /FI "PID eq <PID>"

Stop-Process -Id <PID> -Force
