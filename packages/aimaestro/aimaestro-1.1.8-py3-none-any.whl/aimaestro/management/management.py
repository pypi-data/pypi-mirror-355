# -*- encoding: utf-8 -*-

import os
import json
import pymongo
from flask_sock import Sock
from flask_cors import CORS
from flask_restful import Api
from flask_session import Session
from flask import Flask, request, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash

from aimaestro.aiagent import OpenAIModel
from aimaestro.abcglobal.key import *
from aimaestro.plugins import *

from aimaestro.taskflux import *

script_path = os.path.dirname(__file__)


def authorize():
    authorization = request.headers.get('Authorization')
    session_id = authorization.split('Bearer ')[-1]
    if session_id in session:
        return session_id
    return False


class APIUser:

    def __init__(self, flask_app):
        self.flask_app = flask_app

        flask_app.add_url_rule('/', view_func=self.index, methods=['GET'])
        flask_app.add_url_rule('/<path:path>', view_func=self.serve_vue, methods=['GET'])
        flask_app.add_url_rule('/assets/<path:filename>', view_func=self.serve_static, methods=['GET'])

        flask_app.add_url_rule('/api/user/info', view_func=self.get_user_info, methods=['GET'])
        flask_app.add_url_rule('/api/user/login', view_func=self.user_login, methods=['POST'])
        flask_app.add_url_rule('/api/user/logout', view_func=self.logout, methods=['POST'])

    def index(self):
        return send_from_directory(self.flask_app.static_folder, 'index.html')

    def serve_vue(self, path):
        return send_from_directory(self.flask_app.static_folder, 'index.html')

    def serve_static(self, filename):
        return send_from_directory(os.path.join(self.flask_app.static_folder, 'assets'), filename)

    @staticmethod
    def user_login():
        request_json = request.get_json()
        username = request_json.get('username')
        password = request_json.get('password')
        user_info = query_user_only(query={'username': username}, field={'_id': 0})
        db_password = user_info.get('password')
        if check_password_hash(db_password, password):
            session_id = generate_password_hash(username)
            session[session_id] = username
            return {'code': 20000, 'msg': 'Login successful', 'data': {'token': session_id}}
        return {'code': 50000, 'msg': 'Invalid username or password'}

    @staticmethod
    def logout():
        session_id = authorize()
        if session_id:
            session.pop(session_id, None)
        return {'code': 20000, 'msg': 'Logout successful'}

    @staticmethod
    def get_user_info():
        session_id = authorize()
        if session_id:
            username = session[session_id]
            user_info = query_user_only(query={'username': username}, field={'_id': 0, 'password': 0})
            return {'code': 20000, 'msg': 'Get user info successful', 'data': user_info}
        return {'code': 50001, 'msg': 'Permission verification failed'}


class APIAiAgent:

    def __init__(self, flask_app, sock_app):
        flask_app.add_url_rule('/api/aiagent/dialogues', view_func=self.dialogues, methods=['GET'])
        flask_app.add_url_rule('/api/aiagent/dialogues', view_func=self.delete_dialogues, methods=['DELETE'])
        flask_app.add_url_rule('/api/aiagent/dialogue_message', view_func=self.dialogue_message, methods=['GET'])

        sock_app.route('/ai_dialogue')(self.ws_ai_dialogue)

    @staticmethod
    def dialogues():
        session_id = authorize()
        if session_id:
            username = session[session_id]
            count, dialogues = query_dialogues(
                query={'username': username, 'status': 'active'},
                field={'_id': 0}, limit=15, skip_no=0
            )
            return {'code': 20000, 'msg': 'Get dialogues successful', 'data': dialogues}
        return {'code': 50001, 'msg': 'Permission verification failed'}

    @staticmethod
    def delete_dialogues():
        session_id = authorize()
        if session_id:
            dialogue_id = request.args.get('dialogue_id')
            dialogues_insert_one(
                query={'dialogue_id': dialogue_id},
                data={'status': 'deleted'}
            )
            dialogues_message_insert_one(
                query={'dialogue_id': dialogue_id},
                data={'status': 'deleted'}
            )

            return {'code': 20000, 'msg': 'Delete dialogues successful'}
        return {'code': 50001, 'msg': 'Permission verification failed'}

    @staticmethod
    def dialogue_message():
        session_id = authorize()
        if session_id:
            dialogue_id = request.args.get('dialogue_id')
            count, message = query_dialogue_message(
                query={'dialogue_id': dialogue_id},
                field={'_id': 0}, limit=200, skip_no=0
            )
            return {'code': 20000, 'msg': 'Get dialogues successful', 'data': message}
        return {'code': 50001, 'msg': 'Permission verification failed'}

    @staticmethod
    def save_dialogue(dialogue_id, username, user_message):
        title = user_message[:10]
        dialogue_data = {
            'dialogue_id': dialogue_id,
            'username': username,
            'title': title,
            'create_time': get_converted_time('%Y-%m-%d %H:%M:%S'),
            'update_time': get_converted_time('%Y-%m-%d %H:%M:%S'),
            'status': 'active'
        }
        dialogues_insert_one(query={'dialogue_id': dialogue_id}, data=dialogue_data)
        return title

    @staticmethod
    def get_history_message(dialogue_id):
        count, data = query_dialogue_message(
            query={'dialogue_id': dialogue_id}, field={'_id': 0}, limit=50, skip_no=0)
        history_message = []
        for m in data:
            if m.get('user_message') is not None:
                history_message.append({'role': 'user', 'content': m.get('user_message')})
            if m.get('chatbot_message') is not None:
                history_message.append({'role': 'assistant', 'content': m.get('chatbot_message')})

        return history_message

    @staticmethod
    def save_user_message(dialogue_id, username, user_message):
        message_id = snowflake_id()
        create_time = get_converted_time('%Y-%m-%d %H:%M:%S')
        message_data = {
            'dialogue_id': dialogue_id,
            'message_id': message_id,
            'username': username,
            'user_message': user_message,
            'create_time': create_time
        }
        dialogues_message_insert_one(query={'dialogue_id': dialogue_id, 'message_id': message_id}, data=message_data)
        return message_id, create_time

    @staticmethod
    def save_chatbot_message(message_id, chatbot_message, reasoning_content):
        update_time = get_converted_time('%Y-%m-%d %H:%M:%S')
        message_data = {
            'message_id': message_id,
            'chatbot_message': chatbot_message,
            'chatbot_reasoner': reasoning_content,
            'update_time': update_time
        }
        dialogues_message_insert_one(query={'message_id': message_id}, data=message_data)
        return update_time

    def ws_ai_dialogue(self, ws):
        ws_data = ws.receive(timeout=300)
        ws_json = json.loads(ws_data)
        authorization = ws_json.get('token')
        session_id = authorization.split('Bearer ')[-1]

        dialogue_id = ws_json.get('dialogue_id')
        user_message = ws_json.get('user_message')
        model = ws_json.get('model', 'deepseek-chat')

        if session_id not in session:
            ws.send(json.dumps({
                'type': 'noPermission', 'msg': 'Permission verification failed, please log in again'}))

        username = session[session_id]
        if dialogue_id == '':
            dialogue_id = snowflake_id()
            title = self.save_dialogue(dialogue_id, username, user_message)
            ws.send(json.dumps({
                "type": "dialogueInit",
                "msg": "dialogue init successful",
                "data": {"title": title, "dialogue_id": dialogue_id}}
            ))

        if not user_message:
            ws.send(json.dumps({"type": "error", "msg": "message is empty"}))
            return None

        system_prompt = """
            你是一个专业的内容生成助手，必须严格遵循以下规则：
            1. 所有回复使用 **标准Markdown语法**
            2. 标题层级使用 #、##、### 
            3. 代码块必须标注语言类型
            4. 列表项使用 - 或 1. 
            5. 禁用纯文本段落`;
            """

        history_message = self.get_history_message(dialogue_id)
        history_message.append({'role': 'user', 'content': user_message})
        history_message.insert(0, {'role': 'system', 'content': system_prompt})

        message_id, create_time = self.save_user_message(
            dialogue_id=dialogue_id, username=username,
            user_message=user_message)

        _client = OpenAIModel(temperature=1.0)
        if model == 'deepseek-reasoner':
            response = _client.get_deepseek_reasoner_response(messages=history_message)
            reasoning_content = response.choices[0].message.reasoning_content
            content = response.choices[0].message.content
        else:
            response = _client.get_deepseek_chat_response(messages=history_message)
            reasoning_content = ''
            content = response.choices[0].message.content

        update_time = self.save_chatbot_message(
            message_id=message_id, chatbot_message=content, reasoning_content=reasoning_content)

        ws.send(json.dumps({
            "type": "chatbotMessage",
            "msg": "ok",
            "data": {
                "reasoning_content": reasoning_content,
                "chatbot_message": content,
                'create_time': create_time,
                'update_time': update_time,
            }}
        ))
        return None


class APINodes:

    def __init__(self, flask_app):
        flask_app.add_url_rule('/api/node/list', view_func=self.get_node_list, methods=['GET'])

    @staticmethod
    def get_node_list():
        session_id = authorize()
        if session_id:
            ipaddr = request.args.get('ipaddr')

            page_size = request.args.get('page_size')
            page = request.args.get('page')
            skip_no = int(page_size) * (int(page) - 1)

            query = {}
            if ipaddr is not None and ipaddr != '':
                query['ipaddr'] = ipaddr

            count, data = query_node_list(query=query, field={"_id": 0}, limit=int(page_size), skip_no=skip_no)
            return {'code': 20000, 'msg': 'Get nodes info successful', 'data': data}
        return {'code': 50001, 'msg': 'Permission verification failed'}


class APIServices:

    def __init__(self, flask_app):
        flask_app.add_url_rule('/api/service/list', view_func=self.get_service_list, methods=['GET'])
        flask_app.add_url_rule('/api/service/update_max_process', view_func=self.update_max_process, methods=['POST'])

    @staticmethod
    def get_service_list():
        session_id = authorize()
        if session_id:
            service_name = request.args.get('service_name')
            service_ipaddr = request.args.get('service_ipaddr')

            page_size = request.args.get('page_size')
            page = request.args.get('page')
            skip_no = int(page_size) * (int(page) - 1)

            query = {}
            if service_name is not None and service_name != '':
                query['service_name'] = service_name

            if service_ipaddr is not None and service_ipaddr != '':
                query['service_ipaddr'] = service_ipaddr

            count, data = query_service_list(query=query, field={"_id": 0}, limit=int(page_size), skip_no=skip_no)
            return {'code': 20000, 'msg': 'Get Service list successful', 'data': data}
        return {'code': 50001, 'msg': 'Permission verification failed'}

    @staticmethod
    def update_max_process():
        session_id = authorize()
        if session_id:
            request_json = request.get_json()
            worker_name = request_json.get('worker_name')
            worker_ipaddr = request_json.get('worker_ipaddr')
            worker_max_process = request_json.get('worker_max_process')

            if worker_max_process is None:
                return {'code': 50000, 'msg': 'Invalid worker max process'}

            worker_max_process = int(worker_max_process)

            update_work_max_process(
                worker_name=worker_name, worker_ipaddr=worker_ipaddr, worker_max_process=worker_max_process)
            return {'code': 20000, 'msg': 'Update worker max process successful'}
        return {'code': 50001, 'msg': 'Permission verification failed'}


class APITask:
    def __init__(self, flask_app):
        flask_app.add_url_rule('/api/task/list', view_func=self.get_task_list, methods=['GET'])
        flask_app.add_url_rule('/api/task/stop', view_func=self.stop_task, methods=['POST'])
        flask_app.add_url_rule('/api/task/retry', view_func=self.retry_task, methods=['POST'])

    @staticmethod
    def get_task_list():
        session_id = authorize()
        if session_id:
            task_id = request.args.get('task_id')
            status = request.args.get('status')
            weight = request.args.get('weight')
            queue_name = request.args.get('queue_name')

            page_size = request.args.get('page_size')
            page = request.args.get('page')
            skip_no = int(page_size) * (int(page) - 1)

            query = {}
            if task_id is not None and task_id != '':
                query['task_id'] = task_id
            if status is not None and status != '':
                query['status'] = status
            if weight is not None and weight != '':
                query['weight'] = weight
            if queue_name is not None and queue_name != '':
                query['queue_name'] = queue_name
            count, data = query_task_list(query=query, field={"_id": 0}, limit=int(page_size), skip_no=skip_no)
            return {'code': 20000, 'msg': 'Get task list successful', 'data': data}
        return {'code': 50001, 'msg': 'Permission verification failed'}

    @staticmethod
    def stop_task():
        session_id = authorize()
        if session_id:
            request_json = request.get_json()
            task_id = request_json.get('task_id')
            task_stop(task_id=task_id)
            return {'code': 20000, 'msg': 'Stop task successful'}
        return {'code': 50001, 'msg': 'Permission verification failed'}

    @staticmethod
    def retry_task():
        session_id = authorize()
        if session_id:
            request_json = request.get_json()
            task_id = request_json.get('task_id')
            task_retry(task_id=task_id)
            return {'code': 20000, 'msg': 'Retry task successful'}
        return {'code': 50001, 'msg': 'Permission verification failed'}


class Management:

    def __init__(self, config):
        self.flask_app = Flask(os.path.dirname(__file__), static_folder=os.path.join(script_path, 'dist'))
        self.config = config
        self.logger = logger(filename=KEY_PROJECT_NAME, task_id='plugin_management')

        self.default_username = self.config.get(KEY_ADMIN_USERNAME, DEFAULT_VALUE_USERNAME)
        self.default_password = self.config.get(KEY_ADMIN_PASSWORD, DEFAULT_VALUE_PASSWORD)

        self.flask_api, self.sock_app = self.initialization()
        self.registry_api()

    def initialization(self):
        CORS(self.flask_app, resources='/*', supports_credentials=True)

        self.flask_app.config['SESSION_TYPE'] = 'mongodb'
        self.flask_app.config['SESSION_MONGODB_COLLECT'] = 'session'
        self.flask_app.config['SESSION_MONGODB_DB'] = KEY_PROJECT_NAME
        self.flask_app.config['SESSION_MONGODB'] = pymongo.MongoClient(self.config.get(KEY_MONGO_CONFIG))
        self.flask_app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}

        default_user = query_user_only(query={'username': self.default_username}, field={'_id': 0})
        if default_user is None:
            self.logger.info(f'Create default user: {self.default_username}')
            insert_user(data={
                'username': self.default_username,
                'password': generate_password_hash(self.default_password),
                'role': 'admin',
                'create_time': get_converted_time('%Y-%m-%d %H:%M:%S'),
                'update_time': get_converted_time('%Y-%m-%d %H:%M:%S'),
                'status': 'active'
            })

        Session(self.flask_app)
        return Api(self.flask_app), Sock(self.flask_app)

    def registry_api(self):
        APIUser(self.flask_app)
        APIAiAgent(self.flask_app, self.sock_app)
        APINodes(self.flask_app)
        APIServices(self.flask_app)
        APITask(self.flask_app)

    def run(self):
        bind = self.config['management'].get('bind', '0.0.0.0')
        port = int(self.config['management'].get('port', 15673))
        debug = self.config['management'].get('debug', False)
        enable = self.config['management'].get('enable', False)
        if enable:
            self.flask_app.run(host=bind, port=port, debug=debug)
