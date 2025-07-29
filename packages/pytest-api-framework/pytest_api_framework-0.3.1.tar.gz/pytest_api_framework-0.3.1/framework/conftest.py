import os
import re
import sys
import copy
import importlib
import traceback
from pathlib import Path
from itertools import chain
from urllib.parse import urljoin
from collections import OrderedDict

import dill
import retry
import allure
import pytest
from box import Box

from framework.exit_code import ExitCode
from framework.utils.log_util import logger
from framework.render_data import RenderData
from framework.utils.yaml_util import YamlUtil
from framework.allure_report import generate_report
from framework.global_attribute import CONTEXT, CONFIG
from framework.utils.common import snake_to_pascal, get_apps
from config.settings import DATA_DIR, CASES_DIR

all_app = get_apps()


def pytest_configure(config):
    """
    初始化时被调用，可以用于设置全局状态或配置
    :param config:
    :return:
    """

    for app in all_app:
        # 将所有app对应环境的基础测试数据加到全局
        CONTEXT.set_from_yaml(f"config/{app}/context.yaml", CONTEXT.env, app)
        # 将所有app对应环境的中间件配置加到全局
        CONFIG.set_from_yaml(f"config/{app}/config.yaml", CONTEXT.env, app)
    CONTEXT.set(key="all_app", value=all_app)
    sys.path.append(CASES_DIR)
    CONTEXT.set(key="_http", value=login())


def pytest_addoption(parser):
    parser.addini(name="ignore_error_and_continue", help="是否忽略失败case,继续执行")


def find_data_path_by_case(app, case_file_name):
    """
    基于case文件名称查找与之对应的yml文件路径
    :param app:
    :param case_file_name:
    :return:
    """
    for file_path in Path(os.path.join(DATA_DIR, app)).rglob(f"{case_file_name}.y*"):
        if file_path:
            return file_path


def __init_allure(params):
    """设置allure中case的 title, description, level"""
    case_level_map = {
        "p0": allure.severity_level.BLOCKER,
        "p1": allure.severity_level.CRITICAL,
        "p2": allure.severity_level.NORMAL,
        "p3": allure.severity_level.MINOR,
        "p4": allure.severity_level.TRIVIAL,
    }
    allure.dynamic.title(params.get("title"))
    allure.dynamic.description(params.get("describe"))
    allure.dynamic.severity(case_level_map.get(params.get("level")))
    allure.dynamic.feature(params.get("module"))
    allure.dynamic.story(params.get("describe"))


def pytest_generate_tests(metafunc):
    """
    生成（多个）对测试函数的参数化调用
    :param metafunc:
    :return:
    """
    # 获取当前待执行用例的文件名
    module_name = metafunc.module.__name__.split('.')[-1]
    func_file_path = metafunc.module.__file__
    # 获取当前待执行用例的函数名
    func_name = metafunc.function.__name__
    if func_name in ["test_setup", "test_teardown"]:
        return
    # 获取测试用例所属app
    belong_app = Path(func_file_path).relative_to(CASES_DIR).parts[0]
    # 获取当前用例对应的测试数据路径
    data_path = find_data_path_by_case(belong_app, module_name)

    if not data_path:
        logger.error(f"测试数据文件: {func_file_path} 不存在")
        traceback.print_exc()
        pytest.exit(ExitCode.CASE_YAML_NOT_EXIST)
    test_data = YamlUtil(data_path).load_yml()
    # 测试用例公共数据
    case_common = test_data.get("case_common")
    parametrize = case_common.get("parametrize")
    # 测试用例数据
    case_data = test_data.get(func_name)
    if not case_data:
        logger.error(f"测试方法: {func_name} 对应的测试数据不存在")
        traceback.print_exc()
        pytest.exit(ExitCode.CASE_DATA_NOT_EXIST)
    if case_data.get("request") is None:
        case_data["request"] = dict()
    if case_data.get("request").get("headers") is None:
        case_data["request"]["headers"] = dict()

    # 合并测试数据
    case_data.setdefault("module", case_common.get("module"))
    case_data.setdefault("describe", case_common.get("describe"))
    case_data["_belong_app"] = belong_app

    domain = CONTEXT.get(key="domain", app=belong_app)
    domain = domain if domain.startswith("http") else f"https://{domain}"
    url = case_data.get("request").get("url")
    method = case_data.get("request").get("method")
    if not url:
        if not case_common.get("url"):
            logger.error(f"测试数据request中缺少必填字段: url", case_data)
            pytest.exit(ExitCode.YAML_MISSING_FIELDS)
        case_data["request"]["url"] = urljoin(domain, case_common.get("url"))
    else:
        case_data["request"]["url"] = urljoin(domain, url)

    if not method:
        if not case_common.get("method"):
            logger.error(f"测试数据request中缺少必填字段: method", case_data)
            pytest.exit(ExitCode.YAML_MISSING_FIELDS)
        case_data["request"]["method"] = case_common.get("method")

    for key in ["title", "level"]:
        if key not in case_data:
            logger.error(f"测试数据{func_name}中缺少必填字段: {key}", case_data)
            pytest.exit(ExitCode.YAML_MISSING_FIELDS)

    if case_data.get("mark"):
        metafunc.function.marks = [case_data.get("mark"), case_data.get("level")]
    else:
        metafunc.function.marks = [case_data.get("level")]

    if parametrize:
        case_datas = list()
        ids = list()
        for index, item in enumerate(parametrize):
            deep_copied_case_data = copy.deepcopy(case_data)
            try:
                deep_copied_case_data["_parametrize"] = item
                case_datas.append(deep_copied_case_data)
                ids.append(case_data.get("title") + f"#{index + 1}")
            except KeyError as e:
                logger.error(f"parametrize参数化格式不正确:{e}")
                traceback.print_exc()
                pytest.exit(ExitCode.PARAMETRIZE_ATTRIBUTE_NOT_EXIT)

        metafunc.parametrize("data", case_datas, ids=ids, scope="function")
    else:
        # 进行参数化生成用例
        metafunc.parametrize("data", [case_data], ids=[f'{case_data.get("title")}#1'], scope="function")


def pytest_collection_finish(session):
    """获取最终排序后的 items 列表"""
    # 过滤掉item名称是test_setup或test_teardown的
    session.items = [item for item in session.items if item.name not in ["test_setup", "test_teardown"]]

    # 1. 筛选出带井号 名称带'#' 的item，并记录原始索引
    hash_items_with_index = [(index, item) for index, item in enumerate(session.items) if "#" in item.name]

    # 2. 按照 'cls' 对带井号的元素进行分组
    grouped_by_cls = {}
    for index, item in hash_items_with_index:
        cls = item.parent.name
        if cls not in grouped_by_cls:
            grouped_by_cls[cls] = []
        grouped_by_cls[cls].append((index, item))  # 记录索引和元素

    # 3. 对每个 cls 分组内的带井号的元素进行排序
    for cls, group in grouped_by_cls.items():
        group_values = [x[1] for x in group]
        # 获取item#号后面的数字
        pattern = r"#(\d+)]"
        grouped_data = OrderedDict()
        # 按照#号后面的数字进行排序并分组
        for item in group_values:
            index = re.search(pattern, item.name).group(1)
            grouped_data.setdefault(index, []).append(item)
        # 标记每个分组的第一个和最后一个
        for group2 in grouped_data.values():
            group2[0].funcargs["first"] = True
            group2[-1].funcargs["last"] = True

        group_values = list(chain.from_iterable(grouped_data.values()))

        # 4. 将排序后的items放回原列表
        for (original_index, _), val in zip(group, group_values):
            session.items[original_index] = val  # 将反转后的元素替换回原位置


def pytest_collection_modifyitems(items):
    for item in items:
        try:
            marks = item.function.marks
            for mark in marks:
                if isinstance(mark, list):
                    for item in mark:
                        item.add_marker(mark)
                else:
                    item.add_marker(mark)
        except Exception:
            pass


def pytest_runtest_setup(item):
    if item.cls:
        item.cls.http = CONTEXT.get(key="_http")
        item.cls.belong_app = item.callspec.params.get("data").get("_belong_app")
        item.cls.context = CONTEXT
        item.cls.config = CONFIG
    if item.funcargs.get("first"):
        test_object = item.instance
        test_setup = getattr(test_object, "test_setup", None)
        if test_setup:
            try:
                test_setup()
                item.funcargs["setup_success"] = True
            except Exception as e:
                item.funcargs["setup_success"] = False
                traceback.print_exc()
                logger.error(f"{item.location[0]} test_setup方法执行异常:{e}")


def pytest_runtest_call(item):
    """
    模版渲染，运行用例
    :param item:
    :return:
    """

    ignore_error_and_continue = item.config.getini("ignore_error_and_continue")
    if ignore_error_and_continue == "false":
        # setup方法执行失败，则主动标记用例执行失败，不会执行用例
        if item.funcargs.get("setup_success") is False:
            pytest.skip(f"{item.nodeid} test_setup execute error")
        # 判断上一个用例是否执行失败，如果上一个用例执行失败，则主动标记用例执行失败，不会执行用例（解决场景性用例，有一个失败则后续用例判为失败）
        index = item.session.items.index(item)
        current_cls_name = item.parent.name
        # 向前遍历，找到属于同一个类的用例
        pattern = r"#(\d+)]"
        current_turn = re.search(pattern, item.name)
        if current_turn:
            for prev_item in reversed(item.session.items[:index]):  # 只遍历当前 item 之前的
                if prev_item.parent.name == current_cls_name and re.search(pattern, prev_item.name).group(
                        1) == current_turn.group(1):  # 确保是同一个类
                    status = getattr(prev_item, "status", None)  # 访问 _status 属性
                    if status == "skipped":
                        pytest.skip(f"the test_setup method execution error")
                    elif status == "failed":
                        pytest.skip(f"the previous method execution failed")

    # 获取原始测试数据
    origin_data = item.funcargs.get("data")
    __init_allure(origin_data)
    logger.info(f"执行用例: {item.nodeid}")
    # 对原始请求数据进行渲染替换
    rendered_data = RenderData(origin_data).render()
    # 函数式测试用例添加参数data, belong_app
    http = item.funcargs.get("http")
    item.funcargs["data"] = Box(rendered_data)
    item.funcargs["belong_app"] = origin_data.get("_belong_app")
    item.funcargs["config"] = CONFIG
    item.funcargs["context"] = CONTEXT
    # 类式测试用例添加参数http，data, belong_app
    if item.cls:
        item.cls.http = http
        item.cls.data = Box(rendered_data)
        item.cls.belong_app = origin_data.get("_belong_app")
        item.cls.context = CONTEXT
        item.cls.config = CONFIG

    # 获取测试函数体内容
    func_source = re.sub(r'(?<!["\'])#.*', '', dill.source.getsource(item.function))
    # 校验测试用例中是否有断言
    if "assert" not in func_source:
        logger.error(f"测试方法:{item.originalname}缺少断言")
        pytest.exit(ExitCode.MISSING_ASSERTIONS)


def pytest_runtest_teardown(item):
    if item.funcargs.get("last") and getattr(item, "status", None) not in ["skipped", "failed"]:
        test_object = item.instance
        test_teardown = getattr(test_object, "test_teardown", None)
        if test_teardown:
            try:
                test_teardown()
            except Exception as e:
                pytest.fail(f"the test_teardown method execution error: {e}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """拦截 pytest 生成测试报告，移除特定用例的统计"""
    outcome = yield
    report = outcome.get_result()
    # 将测试结果存储到 item 对象的自定义属性 `_test_status`
    if report.when == "call":  # 只记录测试执行阶段的状态，不包括 setup/teardown
        item.status = report.outcome  # 'passed', 'failed', or 'skipped'


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在 pytest 结束后修改统计数据或添加自定义报告"""
    stats = terminalreporter.stats
    # 统计各种测试结果
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    total = passed + failed + skipped
    try:
        pass_rate = round(passed / (total - skipped) * 100, 2)
    except ZeroDivisionError:
        pass_rate = 0
    # 打印自定义统计信息
    terminalreporter.write("\n============ 执行结果统计 ============\n", blue=True, bold=True)
    terminalreporter.write(f"执行用例总数: {passed + failed + skipped}\n", bold=True)
    terminalreporter.write(f"通过用例数: {passed}\n", green=True, bold=True)
    terminalreporter.write(f"失败用例数: {failed}\n", red=True, bold=True)
    terminalreporter.write(f"跳过用例数: {skipped}\n", yellow=True, bold=True)
    terminalreporter.write(f"用例通过率: {pass_rate}%\n", green=True, bold=True)
    terminalreporter.write("====================================\n", blue=True, bold=True)
    # 生成allure测试报告
    generate_report()


def pytest_exception_interact(node, call, report):
    """
    用例执行抛出异常时，将异常记录到日志
    :param node:
    :param call:
    :param report:
    :return:
    """
    if call.excinfo.type is AssertionError:
        logger.error(f"{node.nodeid} failed: {call.excinfo.value}\n")


@pytest.fixture(autouse=True)
def response():
    response = None
    yield response


@pytest.fixture(autouse=True)
def data():
    data: dict = dict()
    yield data


@pytest.fixture(autouse=True)
def belong_app():
    app = None
    yield app


@pytest.fixture(autouse=True)
def config():
    config = None
    yield config


@pytest.fixture(autouse=True)
def context():
    context = None
    yield context


@retry.retry(tries=3, delay=1)
@pytest.fixture(scope="session", autouse=True)
def http():
    yield Http


class Http(object):
    pass


def login():
    module = importlib.import_module("conftest")
    try:
        for app in all_app:
            setattr(Http, app, getattr(module, f"{snake_to_pascal(app)}Login")(app))
        return Http
    except Exception as e:
        logger.error(f"登录{app}异常:{e}")
        traceback.print_exc()
        pytest.exit(ExitCode.LOGIN_ERROR)
        return None
