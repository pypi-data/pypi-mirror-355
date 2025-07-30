from dataclasses import dataclass
from typing import TypedDict, Union

from pandas import DataFrame
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession


class Relation(TypedDict):
    name: str
    getter: list[SQLModel, InstrumentedAttribute]


@dataclass
class PipelineSpec:
    model: SQLModel
    schema: dict[InstrumentedAttribute, Union[str, Relation]]
    source: DataFrame


async def pipeline(session: AsyncSession, spec: PipelineSpec):
    record = {}
    for _, row in spec.source.iterrows():
        for instruction, obj in spec.schema.items():
            if isinstance(obj, str):
                value = row[obj]
            else:
                getter = obj["getter"]
                value = (
                    await session.exec(
                        select(getter[0].id).where(getter[1] == row[obj["name"]])
                    )
                ).one()

            record[instruction.__dict__["name"]] = value
        session.add(spec.model(**record))
    await session.commit()
