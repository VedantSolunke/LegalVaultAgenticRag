from typing import Literal

from pydantic import BaseModel, Field

MappingSource = Literal["jbp123_bns", "nandhakumarg_ipc_bns_transformation"]


class MappingRecord(BaseModel):
    ipc_section_number: int
    bns_section_numbers: list[int] = Field(min_length=1)
    source: MappingSource
    ipc_title: str | None = None
    bns_title: str | None = None
