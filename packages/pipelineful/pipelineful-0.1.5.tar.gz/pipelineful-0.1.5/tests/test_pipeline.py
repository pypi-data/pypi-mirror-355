from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock

from pandas import read_excel
from sqlmodel import Field, SQLModel

from pipelineful import PipelineSpec, pipeline


class MaterialType(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    broke_percent: float


async def test_pipeline():
    df = read_excel(Path(__file__).parent / "fixtures" / "Material_type_import.xlsx")
    field_name = "Процент потерь сырья"

    df[field_name] = df[field_name].apply(lambda x: float(Decimal(str(x)) * 100))
    df_name = "Тип материала"
    spec = PipelineSpec(
        model=MaterialType,
        schema={
            MaterialType.name: df_name,
            MaterialType.broke_percent: field_name,
        },
        source=df,
    )
    mock = AsyncMock()
    await pipeline(mock, spec=spec)
    mock.commit.assert_awaited()
    for call, (_, row) in zip(mock.add.call_args_list, df.iterrows()):
        material_type = call.args[0]
        assert material_type.name == row[df_name]
        assert material_type.broke_percent == row[field_name]
