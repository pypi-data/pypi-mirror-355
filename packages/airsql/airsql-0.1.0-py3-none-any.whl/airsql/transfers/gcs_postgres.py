from io import StringIO

import numpy as np
import pandas as pd
from airflow.models import BaseOperator
from airflow.providers.google.cloud.hooks.gcs import GCSHook  # type: ignore
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2 import sql as psycopg2_sql  # type: ignore
from psycopg2.extras import execute_values  # type: ignore


class GCSToPostgresOperator(BaseOperator):
    def __init__(
        self,
        target_table_name: str,  # Changed from sqlalchemy_model
        bucket_name: str,
        object_name: str,
        postgres_conn_id: str,
        gcp_conn_id: str,
        conflict_columns=None,
        replace=False,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.bucket_name = bucket_name
        self.object_name = object_name
        self.postgres_conn_id = postgres_conn_id
        self.gcp_conn_id = gcp_conn_id
        self.target_table_name = target_table_name
        self.conflict_columns = conflict_columns
        self.replace = replace

    def _grant_table_privileges(self, pg_hook, schema, table_name_simple):
        """Grant all privileges on table to public."""
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        try:
            table_identifier = (
                psycopg2_sql.Identifier(schema, table_name_simple)
                if schema
                else psycopg2_sql.Identifier(table_name_simple)
            )

            grant_sql = psycopg2_sql.SQL(
                'GRANT ALL PRIVILEGES ON {table} TO PUBLIC'
            ).format(table=table_identifier)

            self.log.info(
                f'Granting all privileges on {schema}.{table_name_simple} to PUBLIC'
            )
            cursor.execute(grant_sql)

            conn.commit()
            self.log.info('Table privileges granted successfully')

        except Exception as e:
            conn.rollback()
            self.log.error(f'Failed to grant table privileges: {e}')
            raise
        finally:
            cursor.close()
            conn.close()

    def execute(self, context):  # noqa: PLR0914, PLR0915
        # Download the CSV file from GCS
        gcs_hook = GCSHook(gcp_conn_id=self.gcp_conn_id)
        file_data = gcs_hook.download(
            bucket_name=self.bucket_name, object_name=self.object_name
        )
        pg_hook = PostgresHook(postgres_conn_id=self.postgres_conn_id)
        # Read the CSV file into a DataFrame
        df = pd.read_csv(StringIO(file_data.decode('utf-8')))

        # Parse target table name for schema and simple table name
        if '.' in self.target_table_name:
            schema, table_name_simple = self.target_table_name.split('.', 1)
        else:
            schema = 'public'  # Default schema in Postgres
            table_name_simple = self.target_table_name

        table_name_full = f'{schema}.{table_name_simple}'

        # Get actual column names from the target Postgres table
        self.log.info(f'Fetching schema for Postgres table: {table_name_full}')
        sql_get_columns = """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;"""
        columns_from_db_records = pg_hook.get_records(
            sql_get_columns, parameters=(schema, table_name_simple)
        )

        if not columns_from_db_records:
            raise ValueError(
                f'Could not retrieve column information for table {table_name_full}.'
                ' Ensure the table exists.'
            )

        model_columns = [rec[0] for rec in columns_from_db_records]
        common_columns = [col for col in df.columns if col in model_columns]
        df_filtered = df[common_columns].replace({np.nan: None})

        if self.replace:
            # Instead of replacing the table (which loses permissions),
            # truncate the data and insert new records
            self.log.info(f'Truncating and replacing data in table {table_name_full}')
            self._truncate_and_insert_data(
                pg_hook, schema, table_name_simple, df_filtered
            )
        elif not self.conflict_columns:
            # Simple append using pandas.to_sql
            engine = pg_hook.get_sqlalchemy_engine()
            self.log.info(f'Appending DataFrame to Postgres table {table_name_full}')
            df_filtered.to_sql(
                name=table_name_simple,
                con=engine,
                schema=schema,
                if_exists='append',
                index=False,
                method='multi',  # Uses multi-value INSERTs for efficiency
                chunksize=1000,  # Adjust as needed
            )
            self.log.info('Append to Postgres complete.')
        else:
            # Use psycopg2.extras.execute_values for bulk upsert
            self._upsert_data(pg_hook, schema, table_name_simple, df_filtered)

        # Grant privileges to specified roles after data operations
        self._grant_table_privileges(pg_hook, schema, table_name_simple)

    def _truncate_and_insert_data(
        self, pg_hook, schema, table_name_simple, df_filtered
    ):
        """Truncate table and insert new data to preserve table permissions."""
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        try:
            table_identifier = (
                psycopg2_sql.Identifier(schema, table_name_simple)
                if schema
                else psycopg2_sql.Identifier(table_name_simple)
            )

            # Truncate the table
            truncate_sql = psycopg2_sql.SQL('TRUNCATE TABLE {table}').format(
                table=table_identifier
            )
            self.log.info(f'Truncating table {schema}.{table_name_simple}')
            cursor.execute(truncate_sql)

            # Insert new data using execute_values for efficiency
            insert_cols_ident = [
                psycopg2_sql.Identifier(col) for col in df_filtered.columns
            ]

            insert_sql = psycopg2_sql.SQL(
                'INSERT INTO {table} ({columns}) VALUES %s'
            ).format(
                table=table_identifier,
                columns=psycopg2_sql.SQL(', ').join(insert_cols_ident),
            )

            # Prepare data for execute_values: list of tuples
            data_tuples = [tuple(x) for x in df_filtered.to_numpy()]

            execute_values(
                cursor,
                insert_sql.as_string(cursor),
                data_tuples,
                page_size=1000,
            )

            conn.commit()
            self.log.info('Truncate and insert to Postgres complete.')

        except Exception as e:
            conn.rollback()
            self.log.error(f'Failed to truncate and insert records: {e}')
            raise
        finally:
            cursor.close()
            conn.close()

    def _upsert_data(self, pg_hook, schema, table_name_simple, df_filtered):
        """Perform upsert operation using ON CONFLICT."""
        table_full_name = f'{schema}.{table_name_simple}'
        self.log.info(f'Upserting DataFrame into Postgres table {table_full_name}')
        conn = pg_hook.get_conn()
        cursor = conn.cursor()

        try:
            # Prepare for psycopg2.sql quoting
            table_identifier = (
                psycopg2_sql.Identifier(schema, table_name_simple)
                if schema
                else psycopg2_sql.Identifier(table_name_simple)
            )

            # Columns for INSERT part
            insert_cols_ident = [
                psycopg2_sql.Identifier(col) for col in df_filtered.columns
            ]

            # Columns for ON CONFLICT part
            conflict_cols_ident = [
                psycopg2_sql.Identifier(col) for col in self.conflict_columns
            ]

            audit_cols_to_exclude = {
                'criado_em',
                'atualizado_em',
                'created_at',
                'updated_at',
            }
            update_set_cols = [
                col
                for col in df_filtered.columns
                if col not in self.conflict_columns
                and col.lower() not in audit_cols_to_exclude
            ]

            if not update_set_cols:
                update_sql_part = psycopg2_sql.SQL('NOTHING')
            else:
                set_statements = [
                    psycopg2_sql.SQL(
                        '{col_to_update} = EXCLUDED.{col_to_update}'
                    ).format(col_to_update=psycopg2_sql.Identifier(col))
                    for col in update_set_cols
                ]
                update_sql_part = psycopg2_sql.SQL('UPDATE SET {}').format(
                    psycopg2_sql.SQL(', ').join(set_statements)
                )

            # Construct the SQL query
            insert_sql = psycopg2_sql.SQL(
                'INSERT INTO {table} ({columns}) VALUES %s'
            ).format(
                table=table_identifier,
                columns=psycopg2_sql.SQL(', ').join(insert_cols_ident),
            )

            conflict_sql_part = psycopg2_sql.SQL(
                'ON CONFLICT ({conflict_cols}) DO '
            ).format(conflict_cols=psycopg2_sql.SQL(', ').join(conflict_cols_ident))

            final_sql_query = psycopg2_sql.SQL(' ').join([
                insert_sql,
                conflict_sql_part,
                update_sql_part,
            ])

            # Prepare data for execute_values: list of tuples
            data_tuples = [tuple(x) for x in df_filtered.to_numpy()]

            execute_values(
                cursor,
                final_sql_query.as_string(cursor),
                data_tuples,
                page_size=1000,
            )
            conn.commit()
            self.log.info('Upsert to Postgres complete.')
        except Exception as e:
            conn.rollback()
            self.log.error(f'Failed to upsert records into database: {e}')
            raise
        finally:
            cursor.close()
            conn.close()
