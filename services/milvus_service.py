from pymilvus import MilvusClient,Collection, CollectionSchema, FieldSchema, DataType, connections,utility
from app.models.survey import SurveyItem
from app.services.hive_service import *
from app.agents.embedder import embed_query_batch,generate_embedding
from app.utils import clean_string_list,clean_milvus_results,split_into_chunks
import pandas as pd
import logging
import os
from app.core import settings


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MilvusService:
    def __init__(self):
        connections.connect(alias="default",host=settings.milvus_host,port=settings.milvus_port)
        self.collection_name = "search_collection"
        self.server_addr = f"http://{settings.milvus_host}:{settings.milvus_port}"
        self.client = MilvusClient(uri=self.server_addr,token="root:Milvus")
        self._create_collection_if_not_exist()
        self._create_survey_partition_if_not_exist()
        self._create_console_partition_if_not_exist()
        
    def _create_collection_if_not_exist(self):
        if not utility.has_collection(self.collection_name):
            print("Collection non trouvée, creation ....")
            schema = self.client.create_schema(
                auto_id=False,
                enable_dynamic_fields=True,
            )
            schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True,max_length=300)
            schema.add_field(field_name="doc_id", datatype=DataType.VARCHAR,max_length=300)
            schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
            schema.add_field(field_name="rev", datatype=DataType.INT64)
            schema.add_field(field_name="nom", datatype=DataType.VARCHAR,max_length=300)
            schema.add_field(field_name="langue", datatype=DataType.VARCHAR,max_length=300)
            schema.add_field(field_name="emplacement", datatype=DataType.ARRAY,max_capacity=100,element_type=DataType.VARCHAR,max_length=1000,nullable=True)
            schema.add_field(field_name="accessright", datatype=DataType.ARRAY,max_capacity=4000,element_type=DataType.VARCHAR,max_length=1000,nullable=True)
            schema.add_field(field_name="content", datatype=DataType.VARCHAR, max_length=10000)
            schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=1024)
            schema.add_field(field_name="vector_title", datatype=DataType.FLOAT_VECTOR, dim=1024)
            index_params = self.client.prepare_index_params()
            index_params.add_index(
                field_name="vector",
                index_name="vector_index",
                index_type="AUTOINDEX",
                metric_type="COSINE"
            )
            index_params.add_index(
                field_name="vector_title",
                index_name="vector_title_index",
                index_type="AUTOINDEX",
                metric_type="COSINE"
            )
            index_params.add_index(
                field_name="accessright",
                index_name="accessright_index",
                index_type="AUTOINDEX"
            )
            index_params.add_index(
                field_name="nom",
                index_name="nom_index",
                index_type="AUTOINDEX"
            )
            index_params.add_index(
                field_name="doc_id",
                index_name="doc_id_index",
                index_type="AUTOINDEX"
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                schema=schema,
                index_params=index_params,
                properties = {"mmap.enabled":True},
                # dimension=1024
            )
            
    def _create_survey_partition_if_not_exist(self):
        if not self.client.has_partition(collection_name = self.collection_name,partition_name = "surveys_vector"):            
            self.client.create_partition(
                collection_name = self.collection_name,
                partition_name = "surveys_vector",                
            )
    
    def _create_console_partition_if_not_exist(self):
        if not self.client.has_partition(collection_name = self.collection_name,partition_name = "consoles_vector"):            
            self.client.create_partition(
                collection_name = self.collection_name,
                partition_name = "consoles_vector",                
            )

    def _description_collection(self):
        if utility.has_collection(self.collection_name):
            res = self.client.describe_collection(
                collection_name=self.collection_name
            )
            return res
        
    def _collection_load_state(self):
        if utility.has_collection(self.collection_name):
            res = self.client.get_load_state(
                collection_name=self.collection_name
            )
            return res
    def _survey_partition_load_state(self):
        if self.client.has_partition(collection_name = self.collection_name,partition_name = "surveys_vector"):
            res = self.client.get_load_state(
                collection_name=self.collection_name,
                partition_name="surveys_vector"
            )
            return res
        
    def _console_partition_load_state(self):
        if self.client.has_partition(collection_name = self.collection_name,partition_name = "consoles_vector"):
            res = self.client.get_load_state(
                collection_name=self.collection_name,
                partition_name="consoles_vector"
            )
            return res
            
    def _clean_survey_partition(self):
        if self.client.has_partition(collection_name = self.collection_name,partition_name = "surveys_vector"):
            self.client.release_partitions(
                collection_name=self.collection_name,
                partition_names=["surveys_vector"]
            )
            self.client.drop_partition(
                collection_name=self.collection_name,
                partition_name="surveys_vector"
            )
    def _clean_console_partition(self):
        if self.client.has_partition(collection_name = self.collection_name,partition_name = "consoles_vector"):
            self.client.release_partitions(
                collection_name=self.collection_name,
                partition_names=["consoles_vector"]
            )
            self.client.drop_partition(
                collection_name=self.collection_name,
                partition_name="consoles_vector"
            )
            
    def _clean_collection(self):
        if utility.has_collection(self.collection_name):
            self.client.release_collection(
                collection_name=self.collection_name
            )
            self.client.drop_collection(
                collection_name=self.collection_name
            )
    
    def list_surveys(self):
        filter = 'id is not null'
        results = self.client.query(
            collection_name=self.collection_name,
            partition_names=["surveys_vector"],
            filter=filter,
            output_fields=["id","doc_id","chunk_index","nom","emplacement","content","vector_title"]            
        )
        logger.info(results)
        # for r in results:
        #     if isinstance(r.get("emplacement"), (list, tuple)):
        #         r["emplacement"] = list(r["emplacement"])
        #     if isinstance(r.get("accessright"), (list, tuple)):
        #         r["accessright"] = list(r["accessright"])

        clean_data = []
        for row in results:
            item = dict(row)  # force le cast HybridExtraRow → dict

            # Forcer la conversion des listes non-JSON en liste Python
            for key in ("emplacement", "accessright"):
                if key in item and not isinstance(item[key], list):
                    try:
                        item[key] = list(item[key])
                    except Exception:
                        item[key] = [str(item[key])]  # fallback
            clean_data.append(item)
        results = clean_data
        logger.info(results)

        return results

    def list_consoles(self):
        filter = 'id is not null'
        results = self.client.query(
            collection_name=self.collection_name,
            partition_names=["consoles_vector"],
            filter=filter,
            output_fields=["id","doc_id","chunk_index","nom","emplacement","content","vector_title"]            
        )
        clean_data = []
        for row in results:
            item = dict(row)  
            for key in ("emplacement", "accessright"):
                if key in item and not isinstance(item[key], list):
                    try:
                        item[key] = list(item[key])
                    except Exception:
                        item[key] = [str(item[key])]  
            clean_data.append(item)
        results = clean_data
        return results
    

    def delete_ids(self, ids, partition):
        if not ids or len(ids)==0:
            message = "Aucun "+partition+" à supprimer."
            logger.info(message)
            return message

        filter = "id in ["+ ids +"]"

        self.client.delete(
            collection_name=self.collection_name,
            partition_name=partition+"s_vector",
            filter = filter
        )
        message = f"{len(ids)} "+partition+"s supprimés dans Milvus."
        return message
    
    def bulk_insert_surveys_to_milvus(self):
        surveys = fetch_surveys_to_create()
        message = ""
        if not surveys:
            message = "Aucun survey à insérer."
            logger.info(message)
            return message
        df = pd.DataFrame([survey.dict() for survey in surveys])
        df['emplacement'] = df['emplacement'].apply(lambda x: x if isinstance(x, list) else [])
        df['accessright'] = df['accessright'].apply(lambda x: x if isinstance(x, list) else [])
        # vectors = embed_query_batch(df["content"].tolist())         
        # delete ids 
        ids = [survey.id for survey in surveys]
        logger.warning(ids)
        id_string = ",".join(f"'{id_}'" for id_ in ids)
        self.delete_ids(id_string,"survey")
        logger.warning(f"{len(ids)} surveys supprimés dans Milvus.")
        insert_data = []
        for i, row in df.iterrows():
            doc_id = row["id"]
            content_chunks = split_into_chunks(row["content"])
            if not content_chunks:
                logger.warning(f"Aucun chunk généré pour {doc_id}")
                continue
            chunk_vectors = embed_query_batch(content_chunks) 
            title_vectors = generate_embedding(row["nom"])
            logger.warning(f"doc {doc_id} ")
            for idx, chunk_text in enumerate(content_chunks):
                logger.warning(f"chunk {idx} ")
                insert_data.append({
                    "id": f"{doc_id}_{idx}",
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "rev": row.get("rev", 0),
                    "nom": row.get("nom", ""),
                    "langue": row.get("langue", ""),
                    "emplacement": row.get("emplacement", []),
                    "accessright": row.get("accessright", []),
                    "content": chunk_text[:10000],  # Truncation sécurité
                    "vector": chunk_vectors[idx],
                    "vector_title": title_vectors,
                })
        if not insert_data:
            logger.warning("Aucune donnée insérée dans Milvus (tous les contenus vides ?)")
            return "Aucun insert réalisé"                       
        logger.warning(f"Insertion de {len(insert_data)} chunks dans Milvus.")
        self.client.upsert(
            collection_name=self.collection_name,
            partition_name="surveys_vector",
            data=insert_data
        )
        message = f"{len(insert_data)} chunks insérés dans Milvus."
        logger.info(message)
        return message

    def bulk_insert_consoles_to_milvus(self):
        consoles = fetch_consoles_to_create()
        message = ""
        if not consoles:
            message = "Aucun console à insérer."
            logger.info(message)
            return message
        df = pd.DataFrame([console.dict() for console in consoles])
        df['emplacement'] = df['emplacement'].apply(lambda x: x if isinstance(x, list) else [])    
        # delete ids 
        ids = [console.id for console in consoles]
        logger.warning(ids)
        id_string = ",".join(f"'{id_}'" for id_ in ids)
        self.delete_ids(id_string,"console")
        logger.warning(f"{len(ids)} consoles supprimés dans Milvus.")
        insert_data = []
        for i, row in df.iterrows():
            doc_id = row["id"]
            content_chunks = split_into_chunks(row["content"])
            if not content_chunks:
                logger.warning(f"Aucun chunk généré pour {doc_id}")
                continue
            chunk_vectors = embed_query_batch(content_chunks) 
            title_vectors = generate_embedding(row["nom"])
            logger.warning(f"doc {doc_id} ")
            for idx, chunk_text in enumerate(content_chunks):
                logger.warning(f"chunk {idx} ")
                insert_data.append({
                    "id": f"{doc_id}_{idx}",
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "rev": row.get("rev", 0),
                    "nom": row.get("nom", ""),
                    "langue": row.get("langue", ""),
                    "emplacement": row.get("emplacement", []),
                    "content": chunk_text[:10000], 
                    "vector": chunk_vectors[idx],
                    "vector_title": title_vectors,
                })
        if not insert_data:
            logger.warning("Aucune donnée insérée dans Milvus (tous les contenus vides ?)")
            return "Aucun insert réalisé"                       
        logger.warning(f"Insertion de {len(insert_data)} chunks dans Milvus.")
        self.client.upsert(
            collection_name=self.collection_name,
            partition_name="consoles_vector",
            data=insert_data
        )
        message = f"{len(insert_data)} chunks insérés dans Milvus."
        logger.info(message)
        return message


    def delete_surveys_milvus(self):
        ids = fetch_surveys_to_delete()
        self.delete_ids( "','".join(f"'{id}'" for id in ids),"survey" )
    


    def search(self,query):
        query_vector = generate_embedding(query)
        res = self.client.search(
            collection_name=self.collection_name,
            data=[query_vector],
            limit=2,
            search_params={"metric_type": "COSINE"},
            partition_names=["surveys_vector"],
            # filter='partition_key in ["459923178704175677"]',
            # filter="ARRAY_CONTAINS_ANY(history_temperatures, [23, 24])",
            output_fields=["id","doc_id","chunk_index","nom","emplacement","content"]
            )
        logger.warning(res)

        res = clean_milvus_results(res)
        clean_data = []
        for row in res:
            item = dict(row)  # force le cast HybridExtraRow → dict

            # Forcer la conversion des listes non-JSON en liste Python
            for key in ("emplacement", "accessright"):
                if key in item and not isinstance(item[key], list):
                    try:
                        item[key] = list(item[key])
                    except Exception:
                        item[key] = [str(item[key])]  # fallback
            clean_data.append(item)
        logger.warning(res)
        res = clean_data
        
        return res
    
    