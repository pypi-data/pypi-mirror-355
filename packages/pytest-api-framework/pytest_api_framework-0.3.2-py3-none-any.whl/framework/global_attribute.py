import os
import traceback

import pytest
from box import Box, BoxList
from box.exceptions import BoxError

from config.settings import ROOT_DIR
from framework.exit_code import ExitCode
from framework.utils.log_util import logger
from framework.utils.common import singleton


class GlobalAttribute(object):
    def __setattr__(self, key, value):
        super().__setattr__(
            key,
            Box(value) if isinstance(value, dict) else BoxList(value) if isinstance(value, list) else value
        )

    def __str__(self):
        return Box(self.__dict__).to_json(indent=2)

    def get(self, key, app=None):
        if app:
            obj = getattr(self, app, None)
        else:
            obj = self
        value = getattr(obj, key, None)
        return Box(value) if isinstance(value, dict) else BoxList(value) if isinstance(value, list) else value

    def set(self, key, value, app=None):
        if app:
            key = f"{app}.{key}"
            self.set_by_chain(key, value)
        else:
            setattr(self, key, value)

    def set_by_chain(self, key_chain, value):
        """
        链式格式的key进行set
        :param key_chain:
        :param value:
        :return:
        """
        keys = key_chain.split(".")
        for key in keys[:-1]:
            if not hasattr(self, key):
                setattr(self, key, Box())  # 创建一个空对象属性
            self = getattr(self, key)
        setattr(self, keys[-1], value)

    def set_from_dict(self, dic, app=None):
        for k, v in dic.items():
            self.set(k, v, app)

    def set_from_yaml(self, filename, env, app=None):
        try:
            file = os.path.join(ROOT_DIR, filename)
            if not os.path.exists(file):
                logger.error(f"yml文件: {file} 不存在")
                traceback.print_exc()
                pytest.exit(ExitCode.CONTEXT_YAML_NOT_EXIST)
            self.set_from_dict(dict(Box().from_yaml(filename=file).get(env)), app)
        except BoxError:
            logger.error(f"yml文件: {file} 内容不存在")
            traceback.print_exc()
            pytest.exit(ExitCode.CONTEXT_YAML_DATA_FORMAT_ERROR)

    def delete(self, key):
        delattr(self, key)


@singleton
class Context(GlobalAttribute):
    ...


@singleton
class Config(GlobalAttribute):
    ...


@singleton
class FrameworkContext(GlobalAttribute):
    ...


# 创建管理变量的全局对象，用于存储临时变量
CONTEXT = Context()
# 创建配置内容管理的全局对象
CONFIG = Config()

_FRAMEWORK_CONTEXT = FrameworkContext()
