import datetime as dt
from batch_pipeline_classes.BaseProcessor import BaseProcessor
from google.cloud.bigquery import Client, WriteDisposition, QueryJobConfig


class GCPProcessor(BaseProcessor):

    def __init__(self, project_id, region, dataset_id):
        self.project_id = project_id
        self.region = region
        self.dataset_id = dataset_id
        self.bq_client = Client(
            project = self.project_id,
            location = self.region
        )



    def write_to_db(self, data:dict, table_name, mode=""):

        mode = mode.strip().lower()
        wd = WriteDisposition.WRITE_APPEND

        if mode == "overwrite":
            wd = WriteDisposition.WRITE_TRUNCATE

        query = '''
        INSERT INTO {self.dataset_id}.{table_name}
        ({",".join(data.keys()})
        VALUES ({",".join(data.values()})
        '''

        query_job = self.bq_client.query(
            query,
            job_config=QueryJobConfig(
                 write_disposition = wd
            )
        )

        job_done = False
        while not job_done:
            job_done = query_job.done()

        return job_done


    def read_from_db(self, query):

        query_job = self.bq_client.query(query)
        query_result = query_job.result()

        rows_list = []

        for row in query_result:
            row_dict = {}
            for key, val in row.items():
                row_dict[key] = val

            rows_list.append(row_dict)

        return rows_list

    def execute_sql(self, sql_statement: str):

        query_job = self.bq_client.query(sql_statement)
        job_done = False
        while not job_done:
            job_done = query_job.done()

        return job_done

    def load_last_execution_date(self) -> dt.date:
        pass
