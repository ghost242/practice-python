from practice_files.practice_sqlalchemy.model import (
    CreditCard,
    Company,
    Car,
    Human,
    Ownership,
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import factory

from pytest_factoryboy import register


session = scoped_session(sessionmaker())


@register
class CreditCardFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = CreditCard
        sqlalchemy_session = session

    provider = "Samsung"
    bounded = 500000


@register
class CompanyFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Company
        sqlalchemy_session = session

    name = "Volkswagen"
    location = "Germany"


@register
class CarFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Car
        sqlalchemy_session = session

    name = "Beetle"
    drivetrain = "FWD"
    maker_id = factory.SubFactory(CompanyFactory, name="Volkswagen", location="Germany")
    price = 250000


@register
class HumanFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Human
        sqlalchemy_session = session

    name = "Dick"
    credit_card_id = factory.SubFactory(
        CreditCardFactory, provider="Hyundai", bounded=300000
    )


@register
class OwnershipFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Ownership
        sqlalchemy_session = session

    human_id = factory.SubFactory(HumanFactory, name="Jane")
    car_id = factory.SubFactory(
        CarFactory, name="NewBeetle", drivetrain="FWD", price=300000
    )



def test_get_factory_model(company):

    c = session.query(Company).filter(Company.name=="Volkswagen").all()

    assert c

# def test_get_factory_ownership(ownership_hypothesis):
#     # print(ownership)
#     assert ownership_hypothesis.register_num == "abcd2"
