# region Imports

import json
import subprocess
from datetime import datetime
from functools import wraps

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import PyMongoError


# endregion

# region MongoDBFramework
def list_to_tuple(liste):
    return '(%s)' % ', '.join(map(repr, liste))


def handle_mongo_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PyMongoError as e:
            # Otomatik reconnect mekanizması eklenebilir
            return {"success": False, "message": f"MongoDB Error: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"Unexpected Error: {str(e)}"}

    return wrapper


# Özel Encoder (MongoDB -> Redis için)
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return {"$oid": str(obj)}  # ObjectId'yi özel JSON yapısına çevir
        elif isinstance(obj, datetime):
            return {"$date": obj.isoformat()}  # datetime'ı özel JSON yapısına çevir
        return super().default(obj)


# Özel Decoder (Redis -> Uygulama için)
def custom_decoder(dct):
    if "$oid" in dct:
        return ObjectId(dct["$oid"])  # Özel JSON'dan ObjectId'ye dönüşüm
    elif "$date" in dct:
        return datetime.fromisoformat(dct["$date"])  # Özel JSON'dan datetime'a dönüşüm
    return dct


mongo_info = {
    'host': '',
    'port': 27017,
    'username': '',
    'password': '',
    'db_name': '',
    'authSource': 'admin',
}


class MongoDBFramework:
    def __init__(self, host=mongo_info.get("host"), port=mongo_info.get("port"), db_name=mongo_info.get("db_name"), username=mongo_info.get("username"), password=mongo_info.get("password"), collection_name='ornek', valkey_client=None):
        try:
            self.host = host
            self.port = port
            self.db_name = db_name
            self.username = username
            self.password = password
            self.client = MongoClient(host=host, port=port, username=username, password=password, maxPoolSize=50, minPoolSize=10)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self.collection_name = collection_name
            self.status = {"success": True, "message": f"MongoDB veritabanına bağlanıldı: {db_name}"}
            self.valkey_client = valkey_client

        except Exception as e:
            self.status = {"success": False, "message": f"Bağlantı hatası: {str(e)}"}

    @handle_mongo_errors
    def backup(self, backup_directory='./backup'):
        # `mongodump` komutunu kullanarak yedek al
        subprocess.run([
            'mongodump',
            '-h', self.host,
            '--port', str(self.port),
            '-d', self.db_name,
            '-u', self.username,
            '-p', self.password,
            '--authenticationDatabase', 'admin',
            '--out', backup_directory
        ], check=True)
        return {"success": True, "message": f"Yedekleme başarıyla tamamlandı. Yedek: {backup_directory}"}

    @handle_mongo_errors
    def restore(self, backup_directory='./backup'):
        try:
            subprocess.run([
                'mongorestore',
                '-h', self.host,
                '--port', str(self.port),
                '-u', self.username,
                '-p', self.password,
                '--authenticationDatabase', 'admin',
                '--drop',  # Optional: Overwrite
                backup_directory
            ], check=True)
            return {"success": True, "message": f"Geri yükleme başarıyla tamamlandı: {backup_directory}"}
        except subprocess.CalledProcessError as e:
            return {"success": False, "message": f"Geri yükleme hatası: {str(e)}"}

    @handle_mongo_errors
    def connect(self):
        return self.status

    @handle_mongo_errors
    def set_collection(self, collection_name):  # Koleksiyonu ayarlama metodu
        self.collection = self.db[collection_name]

    @handle_mongo_errors
    def insert(self, document):
        result = self.collection.insert_one(document)
        return {"success": True, "message": "Belge başarıyla eklendi.", "id": str(result.inserted_id)}

    @handle_mongo_errors
    def insert_many(self, document_list):
        result = self.collection.insert_many(document_list)
        return {"success": True, "message": "Belgeler başarıyla eklendi.", "ids": [str(id) for id in result.inserted_ids]}

    @handle_mongo_errors
    def or_conditions(self, conditions_list, base_field=None):
        or_clauses = []

        for cond in conditions_list:
            clause = {}
            for field, condition in cond.items():
                if field.startswith('.'):
                    full_field = f"{base_field}{field}" if base_field else field[1:]
                else:
                    full_field = field

                # _id ObjectId dönüşümü
                if full_field in {"_id", "id"} and isinstance(condition, str):
                    try:
                        condition = ObjectId(condition)
                    except Exception:
                        continue

                if isinstance(condition, dict):
                    for op, value in condition.items():
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        if op == "sw":
                            clause[full_field] = {"$regex": f"^{value}", "$options": "i"}
                        elif op == "ew":
                            clause[full_field] = {"$regex": f"{value}$", "$options": "i"}
                        elif op == "sew":
                            import re
                            clause[full_field] = {"$regex": f".*{re.escape(value)}.*", "$options": "i"}
                        elif op in {"gte", "lte", "gt", "lt"}:
                            clause[full_field] = {f"${op}": value}
                        elif op == "in":
                            clause[full_field] = {"$in": value}
                        elif op == "nin":
                            clause[full_field] = {"$nin": value}
                else:
                    clause[full_field] = condition

            if clause:
                or_clauses.append(clause)

        return or_clauses

    @handle_mongo_errors
    def get(self, conditions, base_field=None, sort=None, skip=None, limit=None, group_by=None, valkey=None, ttl=10):
        cache_key = f"mongo_cache:{self.collection_name}::::{list(conditions.items())}::::{base_field}:{sort}:{skip}:{limit}:{group_by}"
        # print("cache_key:", cache_key)

        total_count = None
        if valkey and self.valkey_client:
            cached_data = self.valkey_client.get(cache_key)
            if cached_data:
                print("FROM VALKEY")
                return json.loads(cached_data, object_hook=custom_decoder)

        if group_by:
            pipeline = []

            mongo_conditions = {}

            # OR desteği
            if "or" in conditions and isinstance(conditions["or"], list):
                mongo_conditions["$or"] = self.or_conditions(conditions["or"], base_field)
                conditions.pop("or")

            for field, condition in conditions.items():
                if field.startswith('.'):
                    full_field = f"{base_field}{field}" if base_field else field[1:]
                else:
                    full_field = field

                if isinstance(condition, dict):
                    for op, value in condition.items():
                        if isinstance(value, datetime):
                            value = f"{value.isoformat()}"

                        if op == "sw":
                            mongo_conditions[full_field] = {"$regex": f"^{value}", "$options": "i"}
                        elif op == "ew":
                            mongo_conditions[full_field] = {"$regex": f"{value}$", "$options": "i"}
                        elif op in {"gte", "lte", "gt", "lt"}:
                            mongo_conditions[full_field] = {f"${op}": value}
                else:
                    mongo_conditions[full_field] = condition

            if mongo_conditions:
                pipeline.append({"$match": mongo_conditions})

            group_stage = {
                "$group": {
                    "_id": f"${group_by}",
                    "count": {"$sum": 1}
                }
            }
            pipeline.append(group_stage)

            project_stage = {
                "$project": {
                    "grouped_by": "$_id",
                    # group_by.split('.')[-1]: "$_id", ### gruplanan alan adını yazar
                    "count": 1,
                    "_id": 0
                }
            }
            pipeline.append(project_stage)

            if sort:
                pipeline.append({"$sort": dict(sort)})

            if skip:
                pipeline.append({"$skip": skip})

            if limit:
                pipeline.append({"$limit": limit})

            result = list(self.collection.aggregate(pipeline))

        else:
            mongo_conditions = {}

            # OR desteği
            if "or" in conditions and isinstance(conditions["or"], list):
                mongo_conditions["$or"] = self.or_conditions(conditions["or"], base_field)
                conditions.pop("or")

            for field, condition in conditions.items():
                if field.startswith('.'):
                    full_field = f"{base_field}{field}" if base_field else field[1:]
                else:
                    full_field = field

                # Burada _id özel durumu kontrol ediliyor
                if full_field in {"_id", "id"}:
                    try:
                        # Eğer zaten ObjectId ise sorun yok, değilse dönüştür
                        if isinstance(condition, str):
                            condition = ObjectId(condition)
                        elif isinstance(condition, dict):
                            # Eğer sorgu operatorlü geldiyse örn. {"eq": "id"}
                            for op, val in condition.items():
                                if isinstance(val, str):
                                    condition[op] = ObjectId(val)
                    except Exception as e:
                        print(f"Invalid ObjectId format: {condition} -> {e}")
                        continue  # hatalıysa bu field'ı atla

                # # OR desteği
                # if field == "or" and isinstance(condition, list):
                #     mongo_conditions["$or"] = self.build_or_conditions(condition, base_field)
                #     continue  # bu özel durumu işlediğimiz için atla

                ### AND Koşulları için
                if isinstance(condition, dict):
                    for op, value in condition.items():
                        if isinstance(value, datetime):
                            value = f"{value.isoformat()}"

                        if op == "sw":
                            mongo_conditions[full_field] = {"$regex": f"^{value}", "$options": "i"}

                        elif op == "ew":
                            mongo_conditions[full_field] = {"$regex": f"{value}$", "$options": "i"}

                        elif op == "sew":
                            import re
                            mongo_conditions[full_field] = {"$regex": f".*{re.escape(value)}.*", "$options": "i"}

                        elif op in {"gte", "lte", "gt", "lt"}:
                            mongo_conditions[full_field] = {f"${op}": value}

                        elif op == "in":
                            mongo_conditions[full_field] = {"$in": value}

                        elif op == "nin":
                            mongo_conditions[full_field] = {"$nin": value}


                else:
                    mongo_conditions[full_field] = condition

            query = self.collection.find(mongo_conditions)

            if sort:
                query = query.sort(sort)

            if skip:
                query = query.skip(skip)

            if limit:
                query = query.limit(limit)

            if skip or limit:
                total_count = self.collection.count_documents(mongo_conditions)

            result = list(query)

        result = [doc for doc in result] if result else []

        if valkey and self.valkey_client and result:
            self.valkey_client.set(cache_key, json.dumps(result, cls=JSONEncoder), ex=ttl)

        if total_count:
            return {"result": result, "total_count": total_count}
        else:
            return result

    @handle_mongo_errors
    def sql_op(self, op, full_sub_field, value):
        if op == "sw":
            return f"{full_sub_field} LIKE '{value}%'"
        elif op == "ew":
            return f"{full_sub_field} LIKE '%{value}'"
        elif op == "sew":
            return f"{full_sub_field} LIKE '%{value}%'"
        elif op == "gte":
            return f"{full_sub_field} >= {value}"
        elif op == "lte":
            return f"{full_sub_field} <= {value}"
        elif op == "gt":
            return f"{full_sub_field} > {value}"
        elif op == "lt":
            return f"{full_sub_field} < {value}"
        elif op == "in":
            return f"{full_sub_field} IN {list_to_tuple(value)}"
        elif op == "nin":
            return f"{full_sub_field} NOT IN {list_to_tuple(value)}"
        return None

    @handle_mongo_errors
    def get_sql(self, conditions, base_field=None, sort=None, skip=None, limit=None, group_by=None):
        """
        MongoDB sorgusunun SQL eşdeğerini oluşturur.

        :param conditions: Dictionary. Koşulları içeren sözlük.
        :param base_field: String. Koşullara eklenecek temel alan adı (ör. "contents").
        :param sort: Tuple or List. Sıralama kriterleri.
        :param skip: Integer. Atlama sayısı.
        :param limit: Integer. Getirilecek belge limiti.
        :param group_by: String. Gruplama yapılacak alan.
        :return: SQL sorgusu şeklinde string.
        """

        # Başlangıç SQL sorgusu
        sql_query = "SELECT "

        # Grup bazlı sorgulama yapılacaksa
        if group_by:
            sql_query += f"{group_by}, COUNT(*) as count FROM {self.collection_name}"
        else:
            sql_query += f"* FROM {self.collection_name}"

        condition_clauses = []

        if conditions:
            sql_query += " WHERE "
            for field, condition in conditions.items():

                # Özel OR desteği
                if field == "or" and isinstance(condition, list):
                    or_clauses = []
                    for sub_cond in condition:
                        for sub_field, sub_val in sub_cond.items():
                            if sub_field.startswith('.'):
                                full_sub_field = f"{base_field}{sub_field}" if base_field else sub_field[1:]
                            else:
                                full_sub_field = sub_field

                            if isinstance(sub_val, dict):
                                for op, value in sub_val.items():
                                    or_clauses.append(self.sql_op(op, full_sub_field, value))

                            else:
                                if isinstance(sub_val, str):
                                    # _id İçin Özel Koşul
                                    if full_sub_field == "_id":
                                        or_clauses.append(f"{full_sub_field} = ObjectId('{sub_val}')")
                                    else:
                                        or_clauses.append(f"{full_sub_field} = '{sub_val}'")

                                else:
                                    or_clauses.append(f"{full_sub_field} = {sub_val}")

                    # Parantez içinde ekleyelim
                    condition_clauses.append(f"({' OR '.join(or_clauses)})")
                    continue

                # Normal AND koşulları
                # Eğer field, '.' ile başlıyorsa base_field'e eklenir
                if field.startswith('.'):
                    full_field = f"{base_field}{field}" if base_field else field[1:]
                else:
                    full_field = field

                if isinstance(condition, dict):
                    for op, value in condition.items():
                        if isinstance(value, datetime):
                            value = f"'{value.isoformat()}'"

                        condition_clauses.append(self.sql_op(op, full_field, value))

                else:
                    # Eşitlik durumu için
                    if isinstance(condition, str):
                        # _id İçin Özel Koşul
                        if full_field == '_id':
                            condition_clauses.append(f"{full_field} = ObjectId('{condition}')")
                        else:
                            condition_clauses.append(f"{full_field} = '{condition}'")
                    else:
                        condition_clauses.append(f"{full_field} = {condition}")

            # Bütün koşulları birleştir
            sql_query += " AND ".join(condition_clauses)

        # Grup bazlı sorgu kontrolü
        if group_by:
            sql_query += f" GROUP BY {group_by}"

        # Sıralama eklenmesi
        if sort:
            sort_clause = ", ".join([f"{field} {'ASC' if direction == 1 else 'DESC'}" for field, direction in sort])
            sql_query += f" ORDER BY {sort_clause}"

        # Atlama ve limit eklenmesi
        if limit is not None:
            sql_query += f" LIMIT {limit}"
        if skip is not None:
            sql_query += f" OFFSET {skip}"

        return sql_query

    @handle_mongo_errors
    def update(self, query, new_values):
        # Eğer query'de _id varsa ve stringse, ObjectId'ye çevir
        if "_id" in query and isinstance(query["_id"], str):
            try:
                query["_id"] = ObjectId(query["_id"])
            except Exception as e:
                return {"success": False, "message": f"Geçersiz ObjectId: {e}"}

        result = self.collection.update_one(query, {"$set": new_values})
        if result.modified_count:
            return {"success": True, "message": "Belge başarıyla güncellendi."}
        else:
            return {"success": False, "message": "Güncelleme yapılacak belge bulunamadı."}

    @handle_mongo_errors
    def update_many(self, query, new_values):
        result = self.collection.update_many(query, {"$set": new_values})
        return {"success": True, "message": f"{result.modified_count} belge başarıyla güncellendi."}

    @handle_mongo_errors
    def delete(self, query):
        # Eğer query'de _id varsa ve stringse, ObjectId'ye çevir
        if "_id" in query and isinstance(query["_id"], str):
            try:
                query["_id"] = ObjectId(query["_id"])
            except Exception as e:
                return {"success": False, "message": f"Geçersiz ObjectId: {e}"}

        result = self.collection.delete_one(query)
        if result.deleted_count:
            return {"success": True, "message": "Belge başarıyla silindi."}
        else:
            return {"success": False, "message": "Silinecek belge bulunamadı."}

    @handle_mongo_errors
    def delete_many(self, query):
        result = self.collection.delete_many(query)
        return {"success": True, "message": f"{result.deleted_count} belge başarıyla silindi."}

    @handle_mongo_errors
    def update_between(self, field, start, end, new_values):
        """Belirli bir alan için aralıktaki değerleri güncelle."""
        query = {field: {"$gte": start, "$lte": end}}
        result = self.collection.update_many(query, {"$set": new_values})
        return {"success": True, "message": f"{result.modified_count} belge başarıyla güncellendi."}

    @handle_mongo_errors
    def delete_between(self, field, start, end):
        """Belirli bir alan için aralıktaki değerleri sil."""
        query = {field: {"$gte": start, "$lte": end}}
        result = self.collection.delete_many(query)
        return {"success": True, "message": f"{result.deleted_count} belge başarıyla silindi."}

    @handle_mongo_errors
    def close(self):
        self.client.close()
        return {"success": True, "message": "MongoDB bağlantısı kapatıldı."}

# endregion MongoDBFramework
