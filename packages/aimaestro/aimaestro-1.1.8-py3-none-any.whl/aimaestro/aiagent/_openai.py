# -*- encoding: utf-8 -*-
from openai import OpenAI
from aimaestro.abcglobal import *


class OpenAIModel:

    def __init__(self, temperature: float = 1.0):
        self._temperature = temperature

        self._client = None

        self._app_key = None
        self._base_url = None
        self._config_key = 'OpenAI'

        self._global_config = GlobalVar().global_config

        self._get_config()
        self._get_client()

    def get_deepseek_chat_response(self, messages: list, stream=False, model: str = 'deepseek-chat', ):
        """
        Get the response from the deepseek-chat model.
        param prompt:
        """
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        )
        return response

    def get_deepseek_reasoner_response(self, messages: list, stream=False, model: str = 'deepseek-reasoner', ):
        """
        Get the response from the deepseek-reasoner model.
        param prompt:
        """
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            stream=stream
        )
        return response

    def _get_client(self):
        """
        Get the OpenAI client.
        :return:
        """
        if self._client is None:
            self._client = OpenAI(api_key=self._app_key, base_url=self._base_url)
        return self._client

    def _get_config(self):
        """
        Get the configuration for the OpenAI model.
        :return:
        """
        self._app_key = self._global_config.get(self._config_key)['deepseek'].get('api_key')
        self._base_url = self._global_config.get(self._config_key)['deepseek'].get('base_url')
