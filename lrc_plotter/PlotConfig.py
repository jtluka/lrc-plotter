from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PlotConfig:
    lnst_data_file_path: str
    view: str
    runs: Optional[list[int]] = None
    flows: Optional[list[int]] = None
    ylim: Optional[float] = None
    legend: bool = False
    aggregated_flows: bool = False
