from practice_files.practice_sqlalchemy.model import (
    CreditCard,
    Company,
    Car,
    Human,
    Ownership,
)

from sqlalchemy.engine import create_mock_engine
from sqlalchemy.orm import sessionmaker, scoped_session

import factory

from pytest_factoryboy import register



def dump(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))

engine = create_mock_engine('postgresql://', dump)

session = scoped_session(sessionmaker(bind=engine))


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
