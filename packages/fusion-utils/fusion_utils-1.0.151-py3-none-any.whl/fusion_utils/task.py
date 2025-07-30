import uuid

class Task:
    SQL_TASK = 'sql'
    PYTHON_TASK = 'python'
    current_stage = 1
    QA_STAGE = 999

    def __init__(self, name, query_definition=None, table_alias=None, query=None, is_qa=False, optional=False, stage=1, condition=None, include_html=False, python_callable=None, task_type='sql'):
        self.name = name
        self.optional = optional
        self.query_definition = query_definition
        self.query = query
        self.is_qa = is_qa
        self.condition_str = condition  # Store condition as string
        self.condition = self.get_condition()
        self.table_alias = uuid.uuid4().hex if not table_alias else table_alias
        self.include_html = include_html  # New attribute to include HTML representation of the dataframe
        self.python_callable = python_callable
        self.task_type = task_type

        # Assign the stage
        if is_qa:
            self.stage = Task.QA_STAGE
        else:
            self.stage = int(stage) if isinstance(stage, (int, float)) else Task.current_stage
            Task.current_stage = max(Task.current_stage, self.stage + 1)

    def define_query(self, query_definition):
        self.query_definition = query_definition

    def define_table_alias(self, table_alias):
        self.table_alias = table_alias

    def define_optional(self, optional):
        self.optional = optional

    def get_condition(self):
        """Convert the condition string to a lambda function."""
        try:
            # Convert the string into a lambda function
            condition_func = eval(f"lambda df: {self.condition_str}")
            return condition_func
        except SyntaxError as e:
            raise ValueError(f"Invalid condition string: {self.condition_str}. SyntaxError: {e}")
        except TypeError as e:
            raise ValueError(f"The condition is improperly formatted or invalid: {self.condition_str}. TypeError: {e}")
        except Exception as e:
            raise ValueError(f"An error occurred while evaluating the condition: {self.condition_str}. Error: {e}")
