# content of test_module.py
import pytest
import boto3
from moto import mock_secretsmanager

# fixture 들의 위계 테스트
@pytest.fixture(scope="session")
def sessarg(request):
    print("  SETUP sessarg")
    yield "sessarg fixture"
    print("  TEARDOWN sessarg")

@pytest.fixture(scope="package")
def pkgarg(request):
    print("  SETUP pkgarg")
    yield "pkgarg fixture"
    print("  TEARDOWN pkgarg")

@pytest.fixture(scope="class")
def clsarg(request):
    print("  SETUP clsarg")
    yield "clsarg fixture"
    print("  TEARDOWN clsarg")

@pytest.fixture(scope="module", params=["mod1", "mod2"])
def modarg(request):
    param = request.param
    print("  SETUP modarg", param)
    yield param
    print("  TEARDOWN modarg", param)


@pytest.fixture(scope="function", params=[1, 2])
def otherarg(request):
    param = request.param
    print("  SETUP otherarg", param)
    yield param
    print("  TEARDOWN otherarg", param)

@pytest.fixture()
def list_param():
    return list()

@pytest.fixture(autouse=True)
def param(list_param):
    list_param.append(123)


### module과 function fixture가 서로 파라미터로 적용받고있을 때 어떻게 호출을 받게되는지에 대한 실험 코드
# 1. module > function 순서로 하위단계 fixture에서 상위단계 fixture를 파라미터로 받는 경우 -> SUCCESS
# @pytest.fixture(scope="module")
# def module_fixture():
#     print("Module fixture")
#     return 1

# @pytest.fixture(scope="function")
# def func_fixture(module_fixture):
#     print("function fixture")
#     yield module_fixture
#     module_fixture += 2
    
# 2. function > module 순서로 상위단계 fixture에서 하위단계 fixture를 파라미터로 받는 경우 -> FAILURE
# ScopeMismatch: You tried to access the function scoped fixture func_fixture_2 with a module scoped request object, involved factories:
# @pytest.fixture(scope="function")
# def func_fixture_2():
#     print("function fixture_2")
    
#     return 10

# @pytest.fixture(scope="module")
# def module_fixture_2(func_fixture_2):
#     print("module_fixture_2")
    
#     yield func_fixture_2 
#     func_fixture_2 += 2
    
# @pytest.fixture
# @moto.mock_secretsmanager
# def sec_value():
#     cli = boto3.client("secretsmanager")
    
#     val = ("TestID", "TestSecret")
    
#     cli.put_secret_value(SecretId=val[0], SecretString=val[1])
    
#     return val

def test_moto_secretsmanager():
    with mock_secretsmanager():
        cli = boto3.client("secretsmanager")
        
        sec_value = ("TestID", "TestSecret")
        
        cli.create_secret(Name=sec_value[0], SecretString=sec_value[1])
        
        value = cli.get_secret_value(SecretId=sec_value[0])
        
        assert value["SecretString"] == sec_value[1]

# def test_function_fixture_scope_2(func_fixture):
#     print(func_fixture)

#     assert False

# def test_function_fixture_scope_3(func_fixture):
#     print(func_fixture)

#     assert False

# def test_function_fixture_scope(func_fixture):
#     print(func_fixture)

#     assert False

# def test_module_fixture_scope_2(module_fixture_2):
#     print(module_fixture_2)

#     assert False

# def test_module_fixture_scope_3(module_fixture_2):
#     print(module_fixture_2)

#     assert False

# def test_module_fixture_scope(module_fixture_2):
#     print(module_fixture_2)

#     assert False
    
def test_2(sessarg, pkgarg, clsarg, modarg, otherarg):
    print(sessarg, pkgarg, modarg, clsarg, otherarg)

    assert True

# def test_3(list_param):
#     assert 123 in list_param

