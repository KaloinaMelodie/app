from typing import Optional, Sequence
from app.models.question import User
from pymilvus import MilvusClient,Collection, CollectionSchema, FieldSchema, DataType, connections,utility
from app.models.survey import SurveyItem
from app.services.hive_service import *
from app.agents.embedder import embed_query_batch,generate_embedding
from app.utils import clean_string_list,clean_milvus_results,split_into_chunks
from app.utils import to_jsonable, utf8_truncate
import pandas as pd
import logging
import os
from app.core import settings
from pymilvus import WeightedRanker,AnnSearchRequest



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MilvusService:
    def __init__(self):
        connections.connect(alias="default",uri=f"https://{settings.milvus_host}",token=settings.milvus_apikey ) #host=settings.milvus_host,port=settings.milvus_port
        self.collection_name = "search_collection"
        self.formation_collection_name = "formation_collection"
        # self.server_addr = f"http://{settings.milvus_host}:{settings.milvus_port}"
        self.server_addr = f"https://{settings.milvus_host}" 
        self.client = MilvusClient(uri=self.server_addr,token=settings.milvus_apikey)
        self._create_collection_if_not_exist()
        self._create_formation_collection_if_not_exist()
        self._create_survey_partition_if_not_exist()
        self._create_console_partition_if_not_exist()
        self._create_document_partition_if_not_exist()
        
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
    def _create_formation_collection_if_not_exist(self):
        if not utility.has_collection(self.formation_collection_name):
            print("Collection Formation non trouvée, creation ....")
            schema = self.client.create_schema(
                auto_id=False,
                enable_dynamic_fields=True,
            )
            schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True,max_length=300)
            schema.add_field(field_name="doc_id", datatype=DataType.VARCHAR,max_length=300)
            schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
            schema.add_field(field_name="url", datatype=DataType.VARCHAR,max_length=300)
            schema.add_field(field_name="title", datatype=DataType.VARCHAR,max_length=300)
            schema.add_field(field_name="breadcrumbs", datatype=DataType.JSON,nullable=True)
            schema.add_field(field_name="content",datatype=DataType.VARCHAR, max_length=10000)
            schema.add_field(field_name="images", datatype=DataType.JSON,nullable=True)
            schema.add_field(field_name="gifs", datatype=DataType.JSON,nullable=True)
            schema.add_field(field_name="videos", datatype=DataType.JSON,nullable=True)
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
                field_name="title",
                index_name="title_index",
                index_type="AUTOINDEX"
            )
            index_params.add_index(
                field_name="doc_id",
                index_name="doc_id_index",
                index_type="AUTOINDEX"
            )
            self.client.create_collection(
                collection_name=self.formation_collection_name,
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

    def _create_document_partition_if_not_exist(self):
        if not self.client.has_partition(collection_name = self.collection_name,partition_name = "documents_vector"):            
            self.client.create_partition(
                collection_name = self.collection_name,
                partition_name = "documents_vector",                
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

    def _clean_document_partition(self):
        if self.client.has_partition(collection_name = self.collection_name,partition_name = "documents_vector"):
            self.client.release_partitions(
                collection_name=self.collection_name,
                partition_names=["documents_vector"]
            )
            self.client.drop_partition(
                collection_name=self.collection_name,
                partition_name="documents_vector"
            )
            
    def _clean_collection(self):
        if utility.has_collection(self.collection_name):
            self.client.release_collection(
                collection_name=self.collection_name
            )
            self.client.drop_collection(
                collection_name=self.collection_name
            )
    def _clean_formation_collection(self):
        if utility.has_collection(self.formation_collection_name):
            self.client.release_collection(
                collection_name=self.formation_collection_name
            )
            self.client.drop_collection(
                collection_name=self.formation_collection_name
            )
    
    def list_surveys(self):
        filter = 'id is not null'
        results = self.client.query(
            collection_name=self.collection_name,
            partition_names=["surveys_vector"],
            filter=filter,
             group_by_field="doc_id",
            group_size=1, # p to 2 entities to return from each group otherwise 1 per group
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
            clean_data.append(to_jsonable(item))
        results = clean_data
        logger.info(results)

        return results

    def list_consoles(self):
        filter = 'id is not null'
        results = self.client.query(
            collection_name=self.collection_name,
            partition_names=["consoles_vector"],
            filter=filter,
            output_fields=["id","doc_id","chunk_index","nom","accessright","emplacement","content","vector_title"]            
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
            clean_data.append(to_jsonable(item))
        results = clean_data
        return results
    
    def list_documents(self):
        filter = 'id is not null'
        results = self.client.query(
            collection_name=self.collection_name,
            partition_names=["documents_vector"],
            filter=filter,
            output_fields=["id","doc_id","chunk_index","nom","accessright","emplacement","content","vector_title"]            
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
            clean_data.append(to_jsonable(item))
        results = clean_data
        return results
    
    def list_pages(self):
        filter = 'id is not null'
        results = self.client.query(
            collection_name=self.formation_collection_name,
            filter=filter,
            output_fields=["id","doc_id","chunk_index","title","url","breadcrumbs","images","gifs","videos","content","vector_title"]            
        )
        clean_data = []
        for row in results:
            item = dict(row)  
            for key in ("breadcrumbs"):
                if key in item and not isinstance(item[key], list):
                    try:
                        item[key] = list(item[key])
                    except Exception:
                        item[key] = [str(item[key])]  
            clean_data.append(to_jsonable(item))
        results = clean_data
        return results

    def delete_ids(self, ids, partition):
        if not ids or len(ids)==0:
            message = "Aucun "+partition+" à supprimer."
            logger.info(message)
            return message

        filter = "doc_id in ["+ ids +"]"

        self.client.delete(
            collection_name=self.collection_name,
            partition_name=partition+"s_vector",
            filter = filter
        )
        message = f"{len(ids)} "+partition+"s supprimés dans Milvus."
        return message
    
    def delete_page_ids(self, ids):
        if not ids or len(ids)==0:
            message = "Aucun page à supprimer."
            logger.info(message)
            return message

        filter = "doc_id in ["+ ids +"]"

        self.client.delete(
            collection_name=self.formation_collection_name,
            filter = filter
        )
        message = f"{len(ids)} pages supprimés dans Milvus."
        
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
                    "accessright": row.get("accessright", ["all"]),
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

    def bulk_insert_documents_to_milvus(self):
        documents = fetch_documents_to_create()
        message = ""
        if not documents:
            message = "Aucun document à insérer."
            logger.info(message)
            return message
        df = pd.DataFrame([document.dict() for document in documents])
        df['emplacement'] = df['emplacement'].apply(lambda x: x if isinstance(x, list) else [])    
        # delete ids 
        ids = [document.id for document in documents]
        id_string = ",".join(f"'{id_}'" for id_ in ids)
        self.delete_ids(id_string,"document")
        logger.warning(f"{len(ids)} documents supprimés dans Milvus.")
        insert_data = []
        for i, row in df.iterrows():
            doc_id = row["id"]
            content_chunks = split_into_chunks(row["content"])
            if not content_chunks:
                logger.warning(f"Aucun chunk généré pour {doc_id}")
                continue
            chunk_vectors = embed_query_batch(content_chunks) 
            title_vectors = generate_embedding(row["nom"])
            for idx, chunk_text in enumerate(content_chunks):
                insert_data.append({
                    "id": f"{doc_id}_{idx}",
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "rev": row.get("rev", 0),
                    "nom": row.get("nom", ""),
                    "langue": row.get("langue", ""),
                    "emplacement": row.get("emplacement", []),
                    "accessright": row.get("accessright", ["all"]),
                    "content": utf8_truncate(chunk_text, 10_000),
                    "vector": chunk_vectors[idx],
                    "vector_title": title_vectors,
                })

        if not insert_data:
            logger.warning("Aucune donnée insérée dans Milvus (tous les contenus vides ?)")
            return "Aucun insert réalisé"                       
        logger.warning(f"Insertion de {len(insert_data)} chunks dans Milvus.")
        self.client.upsert(
            collection_name=self.collection_name,
            partition_name="documents_vector",
            data=insert_data
        )
        message = f"{len(insert_data)} chunks insérés dans Milvus."
        logger.info(message)
        return message
    

    def bulk_insert_pages_to_milvus(self):
        pages = fetch_pages_to_create()
        logger.warning(pages)
        message = ""
        if not pages:
            message = "Aucun page à insérer."
            logger.info(message)
            return message
        df = pd.DataFrame([page.dict() for page in pages])
        df['breadcrumbs'] = df['breadcrumbs'].apply(lambda x: x if isinstance(x, list) else [])    
        # delete ids 
        ids = [page.id for page in pages]
        logger.warning(ids)
        id_string = ",".join(f"'{id_}'" for id_ in ids)
        self.delete_page_ids(id_string)
        logger.warning(f"{len(ids)} pages supprimés dans Milvus.")
        insert_data = []
        for i, row in df.iterrows():
            doc_id = row["id"]
            content_chunks = split_into_chunks(row["content"])
            if not content_chunks:
                logger.warning(f"Aucun chunk généré pour {doc_id}")
                continue
            chunk_vectors = embed_query_batch(content_chunks) 
            title_vectors = generate_embedding(row["title"])
            logger.warning(f"doc {doc_id} ")
            for idx, chunk_text in enumerate(content_chunks):
                logger.warning(f"chunk {idx} ")
                insert_data.append({
                    "id": f"{doc_id}_{idx}",
                    "doc_id": doc_id,
                    "chunk_index": idx,
                    "title": row.get("title", ""),
                    "url": row.get("url", ""),
                    "breadcrumbs": row.get("breadcrumbs", []),
                    "images": row.get("images", []),
                    "gifs": row.get("gifs", []),
                    "videos": row.get("videos", []),
                    "content": chunk_text[:10000], 
                    "vector": chunk_vectors[idx],
                    "vector_title": title_vectors,
                })
        if not insert_data:
            logger.warning("Aucune donnée insérée dans Milvus (tous les contenus vides ?)")
            return "Aucun insert réalisé"                       
        logger.warning(f"Insertion de {len(insert_data)} chunks dans Milvus.")
        self.client.upsert(
            collection_name=self.formation_collection_name,
            data=insert_data
        )
        message = f"{len(insert_data)} chunks insérés dans Milvus."
        logger.info(message)
        return message



    def delete_surveys_milvus(self):
        ids = fetch_surveys_to_delete()
        self.delete_ids( ",".join(f"'{id}'" for id in ids),"survey" )
    
    def delete_consoles_milvus(self):
        ids = fetch_consoles_to_delete()
        self.delete_ids( ",".join(f"'{id}'" for id in ids),"console" )

    def delete_documents_milvus(self):
        ids = fetch_documents_to_delete() 
        self.delete_ids( ",".join(f"'{id}'" for id in ids),"document" )


    def search(self,query,user: User, partitions: Optional[Sequence[str]] = None,
):
        query_multimodal_vector = generate_embedding(query)
        # logger.info(",".join(f"'{group}'" for group in user.groups))
        expr="ARRAY_CONTAINS(accessright,'all') or ARRAY_CONTAINS_ANY(accessright, ["+",".join(f"'{group}'" for group in user.groups)+"])"
        search_param_1 = {
        "data": [query_multimodal_vector],
        "anns_field": "vector_title",
        "param": {},
        "limit": 50
        
        }
        request_1 = AnnSearchRequest(**search_param_1,expr=expr)

        search_param_2 = {
        "data": [query_multimodal_vector],
        "anns_field": "vector",
        "param": {},
        "limit": 50
        }
        request_2 = AnnSearchRequest(**search_param_2,expr=expr)
        
        reqs = [request_1, request_2]
        rerank= WeightedRanker(0.8, 0.3)

        res = self.client.hybrid_search(
            # data=[query_multimodal_vector],
            collection_name=self.collection_name,
            reqs=reqs,
            ranker=rerank,
            # anns_field="vector",
            limit=8,
            search_params={"metric_type": "COSINE"}, 
            partition_names=list(partitions) if partitions else [],
             group_by_field="doc_id",
            group_size=2, # p to 2 entities to return from each group otherwise 1 per group
            # filter='partition_key in ["459923178704175677"]',
            output_fields=["id","doc_id","chunk_index","nom","emplacement","content"]
            )
        # logger.info(res)
        MIN_SCORE = 0.85
        res = clean_milvus_results(res)
        res = [r for r in res if r.get("score", 0) >= MIN_SCORE]
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
            clean_data.append(to_jsonable(item))
        res = clean_data
        
        return res
    
    def formation(self,query):
        query_multimodal_vector = generate_embedding(query)
        # logger.info(",".join(f"'{group}'" for group in user.groups))
        search_param_1 = {
        "data": [query_multimodal_vector],
        "anns_field": "vector_title",
        "param": {},
        "limit": 50    
        }
        request_1 = AnnSearchRequest(**search_param_1)
        search_param_2 = {
        "data": [query_multimodal_vector],
        "anns_field": "vector",
        "param": {},
        "limit": 50
        }
        request_2 = AnnSearchRequest(**search_param_2)
        
        reqs = [request_1, request_2]
        rerank= WeightedRanker(0.8, 0.3)

        res = self.client.hybrid_search(
            # data=[query_multimodal_vector],
            collection_name=self.formation_collection_name,
            reqs=reqs,
            ranker=rerank,
            # anns_field="vector",
            limit=3, #8-10
            search_params={"metric_type": "COSINE"}, 
            group_by_field="doc_id",
            group_size=2, # 2-3 
            output_fields=["id","doc_id","chunk_index","title","url","breadcrumbs","images","gifs","videos","content"]
            )
        # logger.info(res)
        MIN_SCORE = 0.85
        res = clean_milvus_results(res)
        res = [r for r in res if r.get("score", 0) >= MIN_SCORE]
        clean_data = []
        for row in res:
            item = dict(row)  
            for key in ("emplacement", "accessright"):
                if key in item and not isinstance(item[key], list):
                    try:
                        item[key] = list(item[key])
                    except Exception:
                        item[key] = [str(item[key])]  
            clean_data.append(to_jsonable(item))
        res = clean_data
        
        return res
    
    