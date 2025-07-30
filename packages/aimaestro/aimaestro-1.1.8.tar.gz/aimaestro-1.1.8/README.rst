aimaestro Description Document
==============================

aimaestro: Intelligent Dispatching
-----------------------------------
1. Automatically call available tools to complete coding, testing, and output final code/test cases/test reports
2. Integrate TaskFlux module to help developers/testers quickly build distributed systems
3. Integrate RPC module, simply set up to complete microservice development
4. Integrate Web automation testing toolchain:
   - Quickly build distributed automation testing system without coding
   - Support multiple formats of report output
5. Integrate crawler toolchain

1. Preparation
--------------

.. code-block:: bash

   pip install aimaestro

   # Install RabbitMQ and initialize the administrator account
   rabbitmqctl add_user scheduleAdmin scheduleAdminPassword
   rabbitmqctl set_user_tags scheduleAdmin administrator
   rabbitmqctl set_permissions -p / scheduleAdmin ".*" ".*" ".*"
   rabbitmqctl list_users

   # Install MongoDB and initialize the administrator account
   mongo
   use admin
   db.createUser({user: "scheduleAdmin", pwd: "scheduleAdminPassword", roles: [{role: "root", db: "admin"}]})

.. note:: Use higher security passwords in production environments.

2. Initialization
-----------------

2.1 config.yaml
~~~~~~~~~~~~~~~

.. code-block:: yaml

    Database:
      mongodb:
        host: 127.0.0.1
        port: 27017
        db: aimaestro
        username: scheduleAdmin
        password: scheduleAdminPassword

    Redis:
      host: 127.0.0.1
      port: 6379
      db: 0
      password: scheduleAdminPassword

    RabbitMQ:
      host: 127.0.0.1
      port: 5672
      username: scheduleAdmin
      password: scheduleAdminPassword

    # Optional parameters, no need to set AI related functions
    OpenAI:
      deepseek:
        api_key: xxxx
        base_url: https://api.deepseek.com/v1

    # Web Management
    management:
      enable: true # is management enabled
      bind: '0.0.0.0'
      port: 15673

    scheduler:
      enable: false

2.2 Initialize
~~~~~~~~~~~~~~

.. code-block:: python

    from aimaestro import *

    ROOT_PATH = os.path.dirname(__file__)
    am = AiMaestro(config_file=config_path, current_dir=ROOT_PATH)

3. TaskFlux
-----------

3.1 Create a Test Project
~~~~~~~~~~~~~~~~~~~~~~~~~

Directory structure::

   .
   ├── test_server
   │   ├── test_server
   │   │   ├── test_server_1.py
   │   │   ├── test_server_2.py
   ├── taskflux_test.py

3.2 test_server Python File Content
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from aimaestro.taskflux import *

   class RpcFunction(ServiceConstructor):
       '''
       Class Name Not modifiable, Define RPC functions
       '''
       service_name = 'test_server'
       test_service_name = 'test_server'

       def get_service_name(self):
           return {"service_name": self.service_name}

       def test_function(self, x, y):
           self.logger.info(f'x == {x}, y == {y}')
           return {"test_service_name": self.test_service_name, 'x': x, 'y': y}

   class WorkerFunction(WorkerConstructor):
       '''
       Class Name Not modifiable, Worker Code
       '''
       worker_name = 'test_server'

       def run(self, data):
           self.logger.info(data)
           source_id = data['task_id']
           subtask_data = [
               {"subtask_name": "test_server_2", "xx": "x1"},
               {"subtask_name": "x2", "xx": "x1"},
               {"subtask_name": "x3", "xx": "x1"},
               {"subtask_name": "x4", "xx": "x5", "task_id": snowflake_id()}
           ]
           subtask_ids = databases_create_subtask(
               subtask_queue='test_server_subtask',
               subtasks=subtask_data,
               source_task_id=source_id
           )
           print(subtask_ids)

3.3 Start Test Service
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from aimaestro.taskflux import *
   from test_server import test_server_1, test_server_2

   am.registry_services(services=[test_server_1, test_server_2])
   am.start_services()

3.4 Example
~~~~~~~~~~~

.. code-block:: python

    from aimaestro.taskflux import *

    # Create a task
    task_id = databases_submit_task(
        task_queue='test_server',
        task_name='test_server',
        task_data={'x': 'x', 'y': 'y'}
    )

    # create subtask
    subtask_id = databases_create_subtask(
        subtask_queue='test_server_subtask',
        subtasks=[{'subtask_name': 'test_server_1', 'x': 'x', 'y': 'y'}],
        source_task_id=task_id
    )

    # stop task
    task_stop(task_id)

    # restart task
    task_retry(task_id)

    # get service list
    query_service_list(query={}, field={}, limit=100, skip=0)

    # get task list
    query_task_list(query={}, field={}, limit=100, skip=0)

    # update_work_max_process
    update_work_max_process(work_name='test_server', worker_ipaddr='127.0.0.1', worker_max_process=10)

    # rpc
    proxy_call(service_name='test_server', method_name='test_function', data={'x': 'x', 'y': 'y'})

    # scheduled tasks
    from xxx import TestTask

    scheduler_add_job(
        job_id='task_1',
        cron_str='0 0/1 * * * *',
        func_object=TestTask(xxx=xxx).test_1
    )

    scheduler_add_job(
        job_id='task_1',
        cron_str='0 0/1 * * * *',
        func_object=TestTask(xxx=xxx).test_2
        args=('x', 'y'),
    )

    scheduler_start()

    # snowflake_id
    _id = snowflake_id()


4. Web Automation Testing
-------------------------

.. code-block:: python


    databases_submit_task(
        queue='web_automation',
        message={
            'task_id': '1897558497262116864',  # Not required, automatically generate snowflake ID
            'primary_classification': 'selenium_automation',  # Required, Software Type
            'secondary_classification': 'test',  # Invalid parameter, station symbol
            'all_save_screenshot': True,  # Whether to save screenshots of each step
            'browser': 'chrome',  # browser type
            'wait_time': 30,  # Default waiting time
            'width': 2560,  # Browser Window width
            'height': 1600,  # Browser Window height
            'params': ['--lang=zh-CN.UTF-8', '--force-device-scale-factor=0.90'],  # Other web driver parameters
            'operations': json.load(open(operations_file, 'r', encoding='utf-8'))  # testing procedure
        }
    )

    # operations_file content
    '''
    Default assertion type: title,text,selected,displayed
    You can use the attribute type to obtain the element attributes
    '''
    [
      {
        "describe": "打开网页",
        "operation_type": "open_url",
        "value": "https://www.baidu.com",
        "sleep": 2,
        "asserts": [
          {
            "assert_type": "title",
            "assert_value": "百度一下，你就知道"
          }
        ]
      },
      {
        "describe": "输入数值",
        "operation_type": "input_text",
        "value": "Pypi aimaestro",
        "sleep": 2,
         # Locating element. Multiple elements can be transferred, but only the first element found will be operated
        "locators": [
          {
            "XPATH": "//*[@id=\"kw3\"]"
          },
          {
            "XPATH": "//*[@id=\"kw\"]"
          }
        ]
      },
      {
        "describe": "点击查询按钮",
        "operation_type": "click",
        "sleep": 2,
        "locators": [
          {
            "XPATH": "//*[@id=\"su\"]"
          }
        ],
        "asserts": [
          {
            "assert_type": "text",
            "assert_value": "百度为您找到以下结果",
            "locators": [
              {
                "XPATH": "//*[@id=\"tsn_inner\"]/div[2]/span"
              }
            ]
          },
          {
            "assert_type": "attribute",
            "expression": "class",  # get attribute name
            "assert_value": "hint_PIwZX c_font_2AD7M", # value
            "locators": [
              {
                "XPATH": "//*[@id=\"tsn_inner\"]/div[2]/span"
              }
            ]
          }
        ]
      },
      {
        "describe": "查询结果截图",
        "operation_type": "save_screenshot",
        "sleep": 2
      }
    ]


4.1 Assertion Types Table:
~~~~~~~~~~~~~~~~~~~~~~~~~~

    +---------------+-------------------------------+
    | Assert Type   | Description                   |
    +===============+===============================+
    | title         | Verify page title             |
    +---------------+-------------------------------+
    | text          | Verify element text content   |
    +---------------+-------------------------------+
    | selected      | Verify element selection      |
    +---------------+-------------------------------+
    | displayed     | Verify element visibility     |
    +---------------+-------------------------------+
    | attribute     | Verify element attribute      |
    +---------------+-------------------------------+
