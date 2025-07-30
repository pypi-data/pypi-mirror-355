from asktable import Asktable


async def get_asktable_data(api_key ,datasource_id, question):
    base_url = "https://api.asktable.com"
    asktable_client = Asktable(base_url= base_url,api_key=api_key)
    answer_response = asktable_client.answers.create(datasource_id=datasource_id, question=question)
    if answer_response.answer is None:
        return "没有查询到相关信息"
    return answer_response.answer.text

async def get_asktable_sql(api_key , datasource_id, question):
    base_url = "https://api.asktable.com"
    asktable_client = Asktable(base_url= base_url,api_key=api_key)
    query_response = asktable_client.sqls.create(datasource_id=datasource_id, question=question)
    if query_response.query.sql is None: 
        return "没有查询到相关信息"
    return query_response.query.sql
