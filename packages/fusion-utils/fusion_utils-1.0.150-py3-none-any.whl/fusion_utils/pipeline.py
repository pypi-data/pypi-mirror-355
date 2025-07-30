import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.cloud import bigquery
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from .task import Task
from .errors import *
import time
import threading
import pandas as pd
import numpy as np
import re
from .fusion_logger import FusionLogger


class Pipeline:
    # Environment configuration
    ENV_CONFIG = {
        'DEV': {
            'dataset_column': 'dev_dataset', 
            'channel_column': 'qa_channel'
        },
        'QA': {
            'dataset_column': 'qa_dataset', 
            'channel_column': 'qa_channel'
        },
        'INTG': {
            'dataset_column': 'intg_dataset', 
            'channel_column': 'prod_channel'
        },
        'PROD': {
            'dataset_column': 'prod_dataset', 
            'channel_column': 'prod_channel'
        }
    }
    
    def __init__(self, name: str, env: str = 'dev'):
        """
        Initialize the Pipeline.

        Args:
            name (str): The name of the pipeline.
            env (str, optional): The environment. Defaults to 'dev'.
        """
        self.name = name
        self.client = bigquery.Client(project='aic-production-core')
        self.env = env.upper()
        
        # Validate environment
        if self.env not in self.ENV_CONFIG:
            raise ValueError(f"Unsupported environment: {self.env}. Supported environments: {list(self.ENV_CONFIG.keys())}")
        
        self.set_table_map()
        self.initialize_datasets()
        self.set_smtp_ip()
        self.halt_execution = False
        self.stages = []
        self.errors = []
        self.qa_queries = []
        self.tasks = []
        self.temp_tables = {}
        self.status = {}
        self.task_execution_times = {}
        self.failed_tasks = []  
        self.logger = self.create_logger()
        self.executed_queries = []
       
    def _get_log_channel(self, dataset='25ba15f5_2d68_4098_96bc_37cc8936c061', table='LKP_LOG_CHANNELS'):
        table_map = f'`{dataset}.{table}`'
        self.table_map_df = self.client.query(f'SELECT * FROM {table_map}').to_dataframe()
        
        # Use environment configuration
        config = self.ENV_CONFIG[self.env]
        channel_column = config['channel_column']
        
        # Try to get the channel for the specific pipeline name
        channel = self.table_map_df.loc[self.table_map_df['pipeline'] == self.name, channel_column]
        # If no specific pipeline found, default to 'ALL' pipeline
        if channel.empty:
            channel = self.table_map_df.loc[self.table_map_df['pipeline'] == 'ALL', channel_column]
        # Ensure we return a single value, even if there are multiple matches for 'ALL'
        return channel.iloc[0]
   
   
    def create_logger(self):
              
        try:
            slack_bot_token = self.client.query(self.translate_tables('Select * from `$Bronze:LKP_SLACK_TOKEN`')).result().to_dataframe().iloc[0,0]
            print('Logger Created!')
            return FusionLogger(slack_bot_token, self._get_log_channel())
        except Exception as e:
            print(f"Failed to create slack logger: {e}")
            return None
        

    def print_initial_summary(self):
        summary = f"""
        Initial Pipeline Summary
        ========================
        Pipeline Name: {self.name}
        Env Mode: {self.env}
        Total Tasks: {len(self.tasks)}
        Total Stages: {len(set(task.stage for task in self.tasks))}
        Tasks by Stage:
        """
        stages = {}
        for task in self.tasks:
            if task.stage not in stages:
                stages[task.stage] = []
            stages[task.stage].append(task)
        
        for stage, tasks in sorted(stages.items()):
            if stage == 999:
                stage = 'QA'
            summary += f"  Stage {stage}:\n"
            for task in tasks:
                summary += f"    - {task.name}\n"
        
        self.logger.log(summary.strip())

    def set_table_map(self, dataset='3349c7ea_09a2_461d_87f5_312a5401c51a', table='LKP_QA_TABLE_MAPPING'):
        table_map = f'`{dataset}.{table}`'
        self.table_map_df = self.client.query(f'SELECT * FROM {table_map}').to_dataframe()
        
        # Use environment configuration
        config = self.ENV_CONFIG[self.env]
        dataset_column = config['dataset_column']
        
        self.dataset_map = dict(zip(
            self.table_map_df['alias'], 
            self.table_map_df[dataset_column]
        ))

    def set_email_recipients(self, recipients):
        if isinstance(recipients, str):
            self.recipients = [recipients]
        else:
            self.recipients = recipients


    def set_smtp_ip(self, dataset='3349c7ea_09a2_461d_87f5_312a5401c51a', table='LKP_SMTP_IP'):
        if '_' not in dataset:
            dataset_id = self.translate_dataset(dataset)
            smtp_map = f'`{dataset_id}.{table}`'
        else:
            smtp_map = f'`{dataset}.{table}`'
        try:
            query = f"SELECT ip FROM {smtp_map} LIMIT 1"
            results = self.client.query(query).result()
            for row in results:
                self.smtp_ip = row['ip']
                break
            if not isinstance(self.smtp_ip, str):
                raise ValueError("Retrieved SMTP IP is not a string.")
        except Exception as e:
            raise ValueError('Cannot retrieve SMTP server IP.') from e


    def translate_dataset(self, alias):
        return getattr(self, alias)


    def initialize_datasets(self):
        # Use environment configuration
        config = self.ENV_CONFIG[self.env]
        dataset_column = config['dataset_column']
        
        for _, row in self.table_map_df.iterrows():
            alias = row['alias']
            dataset = row[dataset_column]
            setattr(self, alias, dataset)


    def translate_tables(self, query):
        for alias, dataset_id in self.dataset_map.items():
            query = query.replace(f'${alias}:', f'{dataset_id}.')
        return query


    def translate_query(self, query):
        query = self.translate_tables(query)
        for alias, table_name in self.temp_tables.items():
            query = query.replace(f'${{{alias}}}', table_name)
        return query
    

    def print_elapsed_time(self, start_time, stop_event):
        while not stop_event.is_set():
            elapsed_time = time.time() - start_time
            self.logger.log(f"Elapsed time: {elapsed_time:.2f} seconds", 'info')
            time.sleep(10)  # Adjust the sleep interval as needed


    def send_email(self, subject, body, recipients=None):
        if not hasattr(self, 'smtp_ip'):
            raise SMTPConfigurationError("SMTP server IP is not configured.")

        if not recipients:
            if hasattr(self, 'recipients'):
                recipients = self.recipients
            else:
                raise SMTPConfigurationError('No recipient passed or defined within pipeline attributes.')

        if isinstance(recipients, str):
            recipients = [recipients]

        sender = 'pinapps@jdpa.com'
        message = MIMEMultipart()
        message['From'] = sender
        message['To'] = ", ".join(recipients)
        message['Subject'] = subject
        css = '<style>.pass { color: #008000; } .fail { color: #FF0000; }</style>'
        body_html = f"<html><head>{css}</head><body>{body}</body></html>"
        message.attach(MIMEText(body_html, 'html'))

        self.logger.attach_to_email(message)
        if self.executed_queries:
            self.logger.attach_queries_to_email(message, self.executed_queries)

        try:
            server = smtplib.SMTP(self.smtp_ip, 25)
            server.ehlo()
            server.sendmail(sender, recipients, message.as_string())
            server.quit()
        except Exception as e:
            self.logger.log(f"Failed to send email: {str(e)}", 'error')


    def execute_query(self, query, temp_table_name=None):
        query = self.translate_query(query)
        self.executed_queries.append(query)
    # -----------------------------
        elapsed_time_thread = None  # Ensure the variable is defined at the start
        stop_event = threading.Event()
        try:
            start_time = time.time()
            elapsed_time_thread = threading.Thread(target=self.print_elapsed_time, args=(start_time, stop_event))
            elapsed_time_thread.start()

            ddl_patterns = [
                r"create\s+table", r"execute\s", r"replace\s+table", r"insert\s+into", r"drop\s+table",
                r"alter\s+table", r"truncate\s+table", r"\bupdate\b", r"delete\s+from"
            ]

            is_ddl = any(re.search(pattern, query.lower()) for pattern in ddl_patterns)

            if temp_table_name and not is_ddl:
                job_config = bigquery.QueryJobConfig(
                    destination=temp_table_name,
                    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                )
                query_job = self.client.query(query, job_config=job_config)
            else:
                query_job = self.client.query(query)

            query_job.result()

            stop_event.set()
            elapsed_time_thread.join()

            end_time = time.time()
            total_elapsed_time = end_time - start_time
            self.logger.log(f"\nQuery executed in {total_elapsed_time:.2f} seconds.")

            if not is_ddl:
                self.create_temp_table(query_job, temp_table_name)
                self.update_temp_table_list(query, temp_table_name)

            return query_job, total_elapsed_time

        except Exception as e:
            if elapsed_time_thread:
                stop_event.set()
                elapsed_time_thread.join()
            error_message = str(e).split('\n\n')[0].strip()
            self.logger.log(f"Failed to execute query: {error_message}", 'error')
            self.logger.log(f"Query: {query}", 'debug')
            raise TaskError(f"Failed to execute query: {error_message}")

 
    def create_temp_table(self, query_job, temp_table_name):
        try:
            destination = query_job.destination
            if destination is None:
                self.logger.log(f"No destination table created for job: {query_job.job_id}")
                return None

            table = self.client.get_table(destination)
            if table.table_type != 'TEMPORARY':
                table.expires = datetime.datetime.now() + datetime.timedelta(hours=1)
                self.client.update_table(table, ["expires"])
                self.logger.log(f"Temporary table {temp_table_name} created.")
            else:
                self.logger.log(f"Skipping expiration update for anonymous table {destination}")
            return temp_table_name
        except Exception as e:
            error_message = str(e).split('\n\n')[0].strip()
            self.logger.log(f"Failed to create temporary table {temp_table_name}: {error_message}", 'error')
            raise TaskError(f"Failed to create temporary table {temp_table_name}: {error_message}")


    def log_task_execution(self, task_name, data_size, elapsed_time):
        try:
            if "test" in task_name.lower():
                self.logger.log(f"Skipping logging for test task: {task_name}")
                return

            log_query = f"""
            INSERT INTO `{self.translate_dataset('Silver')}.LKP_TASK_LOG` (task_name, data_size, date_run, elapsed_time)
            VALUES ('{task_name}', {data_size}, '{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', {elapsed_time})
            """
            self.client.query(log_query).result()
            self.logger.log(f"Logged task execution for task: {task_name}")
        except Exception as e:
            self.logger.log(f"Failed to log task execution for task: {task_name}. Error: {str(e)}", 'error')


    def add_task(self, task):
        self.tasks.append(task)
        if task.is_qa:
            temp_table = None
        else:
            temp_table = f"{self.client.project}.AIC_BRANCH_JOB.{task.table_alias}"
        task.temp_table = temp_table


    def add_external_task(self, df: pd.DataFrame, temp_table_name: str):
        dataset_id = "AIC_BRANCH_JOB"
        table_ref = f"{self.client.project}.{dataset_id}.{temp_table_name}"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        
        load_job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
        load_job.result()

        query_job = type('QueryJob', (object,), {'destination': table_ref})
        
        self.create_temp_table(query_job, temp_table_name)
        self.temp_tables[temp_table_name] = table_ref


    def _execute_stage(self, stage_tasks):
        stage_start_time = time.time()
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.execute_task, task): task for task in stage_tasks}
            for future in as_completed(futures):
                task = futures[future]
                try:
                    future.result()
                except Exception as e:
                    error_message = f"Task '{task.name}' in stage {task.stage} failed with exception: {e}"
                    self.errors.append(error_message)
                    self.logger.log(error_message, 'error')
                    if not task.optional:
                        self.halt_execution = True
                        return
        stage_end_time = time.time()
        return stage_end_time - stage_start_time


    def execute_task(self, task):
        start_time = time.time()
        if task.is_qa:
            self.execute_qa_task(task)

        else:
            self.execute_regular_task(task)
        end_time = time.time()
        self.task_execution_times[task.name] = end_time - start_time


    def log_task_details(self, task):
        task_details = {
            'name': task.name,
            'stage': task.stage,
            'query_definition': task.query_definition,
            'query': getattr(task, 'query', 'Query not translated yet'),
            'is_qa': task.is_qa,
            'optional': task.optional,
            'table_alias': task.table_alias,
            'temp_table': getattr(task, 'temp_table', None)
        }
        self.logger.log(f"Task Details: {task_details}")

    def execute_all(self):
        """
        Execute all tasks in the pipeline, stage by stage, and send a completion email.
        If any errors are encountered, they will be raised at the end of the execution.
        """
        self.print_initial_summary()
        stage_durations = []
        try:
            max_stage = max(task.stage for task in self.tasks)
            stages_executed = set()

            for stage in range(1, max_stage + 1):
                if self.halt_execution:
                    break
                stage_tasks = [task for task in self.tasks if task.stage == stage]
                if stage_tasks and stage not in stages_executed:
                    self.logger.log(f"Executing stage {stage} with {len(stage_tasks)} task(s).")
                    stage_duration = self._execute_stage(stage_tasks)
                    stage_durations.append(stage_duration)
                    stages_executed.add(stage)

            if not self.errors and not self.halt_execution:
                qa_tasks = [task for task in self.tasks if task.stage == Task.QA_STAGE]
                if qa_tasks and Task.QA_STAGE not in stages_executed:
                    self.logger.log(f"Executing stage {Task.QA_STAGE} with {len(qa_tasks)} task(s).")
                    stage_duration = self._execute_stage(qa_tasks)
                    stage_durations.append(stage_duration)
                    stages_executed.add(Task.QA_STAGE)
            else:
                self.logger.log("Skipping QA tasks due to errors in regular tasks.", 'warning')

            self.logger.log("Pipeline execution completed.")
        except Exception as e:
            error_message = f"Pipeline Failure: {e}"
            if self.failed_tasks:
                for failed_task in self.failed_tasks:
                    error_message += f"\nQuery: {failed_task.query}"
            self.errors.append(error_message)
            self.logger.log(error_message, 'error')
        finally:
            if self.errors:
                self.logger.log("Errors encountered during pipeline execution:", 'error')
                for error in self.errors:
                    self.logger.log(error, 'error')
                total_execution_time = sum(duration for duration in stage_durations if duration is not None)

                self.send_completion_email(total_execution_time)
                
                # Raise an error after all tasks have completed if there were any errors
                raise RuntimeError("Errors were encountered during pipeline execution. Check logs for details.")
            else:
                total_execution_time = sum(duration for duration in stage_durations if duration is not None)

                self.send_completion_email(total_execution_time)



    def execute_regular_task(self, task):
        try:
            if task not in self.tasks:
                raise TaskError(f"Task '{task.name}' has not been added to the pipeline. Use Pipeline.add_task() to execute.")

            if not task.query_definition:
                if not task.optional:
                    raise TaskError(f'{task.name} does not have a defined query')
                else:
                    self.logger.log(f'WARNING: {task.name} does not have a defined query. Skipping optional task...', 'warning')
                    self.update_status(task, 'Failed: No query defined')
                    return

            self.update_status(task, 'Started')

            try:
                task.query = self.translate_query(task.query_definition)
            except KeyError as e:
                raise TaskError(f"Failed to translate query for task '{task.name}': Missing key {str(e)} in temp tables")

            estimated_data_size = self.estimate_data_size(task.query)
            self.logger.log(f"Estimated data size for task '{task.name}': {estimated_data_size/1000000000:.2f} Gb")

            estimated_run_time = self.estimate_run_time(estimated_data_size, task.name)
            if estimated_run_time:
                self.logger.log(f"Estimated run time for task '{task.name}': {estimated_run_time:.2f} seconds")

            try:
                temp_table_name = f"{self.client.project}.AIC_BRANCH_JOB.{task.table_alias}"
                query_job, elapsed_time = self.execute_query(task.query, temp_table_name)
                self.update_temp_table_list(task.name, temp_table_name)
                self.log_task_execution(task.name, estimated_data_size, elapsed_time)
                self.update_status(task, 'Completed')
                self.logger.log(f"{task.name} Completed.")
            except Exception as e:
                self.update_status(task, f'Failed: {str(e)}')
                self.logger.log(f"Task '{task.name}' failed with exception: {e}\nQuery: {task.query}", 'error')
                self.log_task_details(task)  # Log task details at the beginning
                if not task.optional:
                    raise e

        except Exception as e:
            error_message = f"Task '{task.name}' in stage {task.stage} failed with exception: {e}\nQuery: {task.query}"
            self.errors.append(error_message)
            self.logger.log(error_message, 'error')
            self.update_status(task, f"Failed with exception: {str(e)}")
            if not task.optional:
                self.halt_execution = True


    def execute_qa_task(self, task):
        self.logger.log(f"Executing QA task '{task.name}'")
        try:
            query = self.translate_query(task.query_definition)
            query_job = self.client.query(query)
            result = query_job.result().to_dataframe()

            if not callable(task.condition):
                raise TaskError(f"Condition for task '{task.name}' is not callable")

            condition_result = task.condition(result)

            if condition_result:
                self.logger.log(f"QA check passed for task '{task.name}'")
                self.update_status(task, 'Completed')
            else:
                self.logger.log(f"QA check failed for task '{task.name}'")
                if task.optional:
                    self.update_status(task, 'Failed (Optional): QA check did not pass')
                else:
                    self.update_status(task, 'Failed: QA check did not pass')

            if task.include_html:
                task.html_result = result.to_html()

        except Exception as e:
            if task.optional:
                self.update_status(task, f'Failed (Optional): {str(e)}')
            else:
                self.update_status(task, f'Failed: {str(e)}')
            self.logger.log(f"QA task '{task.name}' failed with exception: {str(e)}", 'error')


    def execute_task_by_name(self, task_name):
        task = next((t for t in self.tasks if t.name == task_name), None)
        if task is None:
            raise TaskError(f"No task found with name '{task_name}'")
        self.execute_task(task)


    
    def update_temp_table_list(self, task_name, table):
        self.temp_tables[task_name] = f'{table}'

    def update_status(self, task, status):
        update = {'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': status
        }

        if status == 'Completed':
            update['success'] = True
        elif status.startswith('Failed'):
            update['success'] = False

        if task.name not in self.status:
            self.status[task.name] = []
        self.status[task.name].append(update)

    def estimate_data_size(self, query):
        job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
        query_job = self.client.query(query, job_config=job_config)
        return query_job.total_bytes_processed

    def get_historical_data(self):
        query = f"""
        SELECT task_name, data_size, elapsed_time
        FROM `{self.translate_dataset('Silver')}.LKP_TASK_LOG`
        """
        df = self.client.query(query).to_dataframe()
        return df

    def estimate_run_time(self, estimated_data_size, task_name):
        df = self.get_historical_data()
        df_task = df[df['task_name'] == task_name]

        if df_task.empty:
            self.logger.log(f"No historical data available to estimate run time for task '{task_name}'", 'warning')
            return None

        x = df_task['data_size'].values
        y = df_task['elapsed_time'].values
        estimated_time = np.interp(estimated_data_size, x, y)
        return estimated_time

    def send_completion_email(self, total_execution_time):
        regular_status_summary = []
        qa_status_summary = []
        pass_flag = True

        for task_name, updates in self.status.items():
            latest_update = updates[-1]
            execution_time = self.task_execution_times.get(task_name, 'N/A')
            if isinstance(execution_time, (int, float)):
                execution_time_str = f"{execution_time:.2f} seconds"
            else:
                execution_time_str = execution_time
            task_summary = f"<span class='{ 'pass' if latest_update.get('success', False) else 'fail' }'>Task '{task_name}': {latest_update['status']}. (Execution Time: {execution_time_str})</span>"
            task = next((t for t in self.tasks if t.name == task_name), None)
            if task and task.is_qa:
                qa_status_summary.append(task_summary)
                if hasattr(task, 'html_result'):
                    qa_status_summary.append(task.html_result)
            else:
                regular_status_summary.append(task_summary)
            if not latest_update.get('success', False) and not latest_update['status'].startswith('Failed (Optional)'):
                pass_flag = False

        summary = "<br>".join(regular_status_summary)
        qa_summary = "<br>".join(qa_status_summary)
        flag_text = "PASS" if pass_flag else "FAIL"
        total_execution_time_str = f"{total_execution_time:.2f} seconds" if total_execution_time else "N/A"
        run_type = self.env.upper()
        subject = f"{run_type}: {flag_text}: {self.name}"
        body = f"""
        <html>
            <head>
                <style>
                    .pass {{ color: #008000; }}
                    .fail {{ color: #FF0000; }}
                    .header {{ font-weight: bold; font-size: 16px; }}
                    .section {{ margin-bottom: 20px; }}
                    .summary {{ margin-left: 20px; }}
                </style>
            </head>
            <body>
                <div class="section">
                    <div class="header">Pipeline {self.name} Execution Status: {flag_text}</div>
                    <div class="summary">Total Execution Time: {total_execution_time_str}</div>
                </div>
                <div class="section">
                    <div class="header">Regular Tasks:</div>
                    <div class="summary">{summary}</div>
                </div>
                <div class="section">
                    <div class="header">QA Tasks:</div>
                    <div class="summary">{qa_summary}</div>
                </div>
            </body>
        </html>
        """

        try:
            self.send_email(subject, body)
            self.logger.log("Completion email sent successfully.")
        except Exception as e:
            self.logger.log(f"Failed to send completion email: {e}", 'error')


    def set_default_email_recipients(self):
        """
        Set email recipients by fetching from the LKP_FUSION_RECIPIENTS table 
        after translating the dataset and table names.

        This method retrieves the email addresses from the LKP_FUSION_RECIPIENTS table 
        and sets them as the pipeline's recipients.
        """
        try:
            # Define the query to fetch email recipients from the table
            query = 'SELECT email FROM `$Bronze:LKP_FUSION_RECIPIENTS`'

            # Translate the query to resolve dataset and table references
            translated_query = self.translate_query(query)

            # Execute the translated query to fetch email recipients
            results = self.client.query(translated_query).result()
            self.recipients = [row['email'] for row in results]

            # Log the retrieved recipients
            self.logger.log(f"Email recipients set from table: {', '.join(self.recipients)}")

        except Exception as e:
            # Log and raise error if fetching recipients fails
            self.logger.log(f"Failed to set email recipients from table: {e}", 'error')
            raise ValueError("Could not set email recipients from the table.") from e

    def clone_datasets(self, datasets, prod_to_qa=False, qa_to_dev=False, intg_to_qa=False, qa_to_intg=False, prod_to_intg=False, exclude_tables=[]):
        """
        Clones tables from production datasets to QA datasets, excluding specified tables and views.
        """
        clone_options = [prod_to_qa, qa_to_dev, intg_to_qa, qa_to_intg, prod_to_intg]
        if sum(clone_options) != 1:
            raise ValueError('Please specify exactly one clone direction.')
        
        if prod_to_qa:
            source, target = 'prod_dataset', 'qa_dataset'
        elif qa_to_dev:
            source, target = 'qa_dataset', 'dev_dataset'
        elif intg_to_qa:
            source, target = 'intg_dataset', 'qa_dataset'
        elif qa_to_intg:
            source, target = 'qa_dataset', 'intg_dataset'
        elif prod_to_intg:
            source, target = 'prod_dataset', 'intg_dataset'

        # List of datasets to include in cloning
        datasets_formatted = ', '.join(f"'{dataset}'" for dataset in datasets)
        datasets_query = f"SELECT * FROM `3349c7ea_09a2_461d_87f5_312a5401c51a.LKP_QA_TABLE_MAPPING` WHERE alias IN ({datasets_formatted})"
        
        # Get the list of datasets and target datasets
        datasets_result = self.client.query(datasets_query).result()

        for row in datasets_result:
            source_dataset = f'aic-production-core.{row[source]}'
            target_dataset = f'aic-production-core.{row[target]}'

            # Ensure the target dataset exists
            target_dataset_ref = bigquery.Dataset(target_dataset)
            self.client.create_dataset(target_dataset_ref, exists_ok=True)

            # List all tables in the source dataset
            tables = self.client.list_tables(source_dataset)

            for table in tables:
                table_id = table.table_id
                source_table = f"{source_dataset}.{table_id}"
                target_table = f"{target_dataset}.{table_id}"

                # Get the schema of the table
                table_ref = self.client.get_table(source_table)
                schema = table_ref.schema

                # Skip tables with empty schema, views, or excluded tables
                if not schema or table_ref.table_type == 'VIEW' or table_id in exclude_tables:
                    self.logger.log(f"Skipping table {table_id}...", 'info')
                    continue

                # Clone the table
                clone_query = f"""
                CREATE OR REPLACE TABLE `{target_table}` CLONE `{source_table}`;
                """
                job = self.client.query(clone_query)
                job.result()  # Wait for the job to complete
                self.logger.log(f"Cloned table {source_table} to {target_table}", 'info')

        self.logger.log("Table cloning completed.", 'info')


    def send_custom_email(self, subject: str, message: str, recipients: List[str]):
        """
        Sends a custom email using the provided SMTP IP and recipient list.

        Args:
            subject (str): Subject of the email.
            message (str): Body of the email (HTML supported).
            recipients (List[str]): List of email recipients.
            smtp_ip (str): IP address of the SMTP server. Defaults to 'your.smtp.server.ip'.

        Raises:
            ValueError: If SMTP connection or sending the email fails.
        """
        try:
            if isinstance(recipients, str):
                recipients = [recipients]

            sender = 'pinapps@jdpa.com'
            email_message = MIMEMultipart()
            email_message['From'] = sender
            email_message['To'] = ", ".join(recipients)
            email_message['Subject'] = subject

            # HTML body with basic styling
            css = '<style>.pass { color: #008000; } .fail { color: #FF0000; }</style>'
            body_html = f"<html><head>{css}</head><body>{message}</body></html>"
            email_message.attach(MIMEText(body_html, 'html'))

            # Send the email
            with smtplib.SMTP(self.smtp_ip, 25) as server:
                server.ehlo()
                server.sendmail(sender, recipients, email_message.as_string())
                print(f"Email sent successfully to: {', '.join(recipients)}")

        except Exception as e:
            error_message = f"Failed to send email: {str(e)}"
            print(error_message)
            raise ValueError(error_message) from e
