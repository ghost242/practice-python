"""
factoryboy를 이용해서 DB 모델을 모킹하고 pytest fixture로 만들어내는 코드에 대한 두번째 버전.
v1에서 engine, session을 전부 fixture로 만들고 데이터 모델을 fixture화 하는 코드를 포함함.
"""

import factory
import pytest
from pytest_factoryboy import register
from sqlalchemy import create_mock_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import scoped_session, sessionmaker

from practice_files.practice_sqlalchemy import model


@pytest.fixture(scope="module")
def engine_mocker():
    def query_executor(sql, *multiparams, **params):
        print(sql.compile(dialect=engine.dialect))

    engine = create_mock_engine(
        URL.create(
            drivername="postgresql",
            username="admin",
            password="password",
            host="localhost",
            port=5433,
            database="dev_db",
            query=dict(),
        ),
        query_executor
    )
    return engine

@pytest.fixture(scope="module")
def session(engine_mocker):
    return scoped_session(sessionmaker(bind=engine_mocker))

@pytest.fixture(scope="function")
def company_model(session):
    class TestCompanyModel(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = model.Company

            sqlalchemy_session = session

        company_id = 0
        name = "porsche"
        location = "german"

    register(TestCompanyModel)

    return TestCompanyModel()

@pytest.fixture(scope="function")
def ownership_lazy(session):
    @register
    class TestCompanyModel(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = model.Company

            sqlalchemy_session = session

        company_id = 0
        name = "porsche"
        location = "german"



    @register
    class TestCarModel(factory.alchemy.SQLAlchemyModelFactory):
        car_id = 200
        name = "356"
        drivetrain = model.CarType.gasoline
        maker_id = TestCompanyModel.company_id
        price = 2500000

        class Meta:
            model = model.Car

            sqlalchemy_session = session


    @register
    class TestCreditCardModel(factory.alchemy.SQLAlchemyModelFactory):
        card_id = 1234
        provider = "samsung"
        bounded = 1000000

        class Meta:
            model = model.CreditCard

            sqlalchemy_session = session


    @register
    class TestHumanModel(factory.alchemy.SQLAlchemyModelFactory):
        id_number = 1111
        name = "Jamse"
        credit_card_id = 1234

        class Meta:
            model = model.Human

            sqlalchemy_session = session


    @register
    class TestOwnershipModel(factory.alchemy.SQLAlchemyModelFactory):
        human_id = TestHumanModel.id_number
        car_id = TestCarModel.car_id
        register_num = "abcd2"

        class Meta:
            model = model.Ownership

            sqlalchemy_session = session

    return TestOwnershipModel()

# TODO: hyphothesis 패키지를 적용해서 랜덤한 값을 생성하는 fixture를 만들어보는 실험이 필요.
