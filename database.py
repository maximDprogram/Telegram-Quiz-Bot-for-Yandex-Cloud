import os
import ydb
import json


YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")

def get_ydb_pool(ydb_endpoint, ydb_database, timeout=30):
    
    ydb_driver_config = ydb.DriverConfig(
        ydb_endpoint, ydb_database, credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )
    
    ydb_driver = ydb.Driver(ydb_driver_config)
    
    ydb_driver.wait(fail_fast=True, timeout=timeout)
    
    return ydb.SessionPool(ydb_driver)

# Функция форматирования входных аргументов
def _format_kwargs(kwargs):
    return {"${}".format(key): value for key, value in kwargs.items()}

# Функция для выполнения обновляющих запросов
def execute_update_query(pool, query, **kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
    return pool.retry_operation_sync(callee)

# Функция для выполнения выборочных запросов
def execute_select_query(pool, query, **kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
        return result_sets[0].rows
    return pool.retry_operation_sync(callee)

# Инициализация пула соединений
pool = get_ydb_pool(YDB_ENDPOINT, YDB_DATABASE)

# Функция для получения данных вопроса
async def get_question_data(question_index):
    get_question = """
    DECLARE $question_index AS Uint64;
    SELECT question, options, correct_option FROM quiz_questions WHERE question_id == $question_index;
    """
    results = execute_select_query(pool, get_question, question_index=question_index)
    if len(results) == 0:
        return None
    data = results[0]
    
    if isinstance(data['question'], bytes):
        data['question'] = data['question'].decode('utf-8')
    
    data['options'] = json.loads(data['options'] if isinstance(data['options'], (str, bytes)) else data['options'].decode('utf-8'))
    return data