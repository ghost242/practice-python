"""
factoryboy를 이용해서 DB 모델을 모킹하고 pytest fixture로 만들어내는 코드에 대한 초기버전
"""

import factory
import pytest
from pytest_factoryboy import register
from sqlalchemy import engine_from_config
from practice_files.practice_sqlalchemy import model

# from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.engine import create_mock_engine
from sqlalchemy.engine.url import URL

# from pytest_mock_resources import create_mysql_fixture


# mysql_fixture = create_mysql_fixture(
#     model.Base,
#     scope="session",
#     session=True,
#     tables=(
#         model.Ownership,
#         model.Human,
#         model.Car,
#         model.Company,
#         model.CreditCard,
#     ),
# )

def query_executor(sql, *multiparams, **params):
    print(sql.compile(dialect=mock_engine.dialect))

mock_engine = create_mock_engine(
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
session_test = scoped_session(sessionmaker(bind=mock_engine))
print(dir(session_test))

# @pytest.fixture(scope="package")
# def session_test():
    # session = mysql_fixture()
    # session = scoped_session(sessionmaker(bind=mock_engine))
    # print(dir(session))
    # return session


# engine = create_engine("sqlite://", echo=True)
# session = scoped_session(
#     sessionmaker(
#         bind=engine,
#     )
# )


@register
class TestCompanyModel(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = model.Company

        sqlalchemy_session = session_test

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

        sqlalchemy_session = session_test


@register
class TestCreditCardModel(factory.alchemy.SQLAlchemyModelFactory):
    card_id = 1234
    provider = "samsung"
    bounded = 1000000

    class Meta:
        model = model.CreditCard

        sqlalchemy_session = session_test


@register
class TestHumanModel(factory.alchemy.SQLAlchemyModelFactory):
    id_number = 1111
    name = "Jamse"
    credit_card_id = 1234

    class Meta:
        model = model.Human

        sqlalchemy_session = session_test


@register
class TestOwnershipModel(factory.alchemy.SQLAlchemyModelFactory):
    human_id = TestHumanModel.id_number
    car_id = TestCarModel.car_id
    register_num = "abcd2"

    class Meta:
        model = model.Ownership

        sqlalchemy_session = session_test
