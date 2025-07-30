import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

import polars as pl


@dataclass
class GenericDataPacket(ABC):
    source: str
    timestamp: float

    @abstractmethod
    def __str__(self) -> str: ...

    @abstractmethod
    def as_flat_dict(self) -> Dict[str, float | str]: ...

    @abstractmethod
    def as_dataframe(self, add_prefix: bool, time_offset: float | None = None) -> pl.DataFrame: ...

    @abstractmethod
    def __len__(self) -> int: ...


@dataclass
class BinaryDataPacket(GenericDataPacket):
    data: bytes

    def __str__(self):
        return f"(BinaryDataPacket) {self.source} - {len(self.data)} bytes"

    def as_flat_dict(self) -> Dict[str, float | str]:
        raise NotImplementedError("BinaryDataPacket cannot be converted to a flat dictionary")

    def as_dataframe(self, add_prefix: bool, time_offset: float | None = None) -> pl.DataFrame:
        raise NotImplementedError("BinaryDataPacket cannot be converted to a DataFrame")

    def __len__(self):
        return len(self.data)


@dataclass
class SinglePointDataPacket(GenericDataPacket):
    data: Dict[str, float | int | str]  # Contains a single datapoint

    def __str__(self):
        return f"(SinglePointDataPacket) {self.source} - {list(self.data.keys())}"

    def as_flat_dict(self) -> Dict[str, float | str]:
        return {f"{self.source}.{key}": value for key, value in self.data.items()}

    @classmethod
    def from_single_value(cls, node, key: str, value: float | int | str) -> "SinglePointDataPacket":
        return cls(
            source=node.name,
            timestamp=time.time(),
            data={key: value},
        )

    def as_dataframe(self, add_prefix: bool, time_offset: float | None = None) -> pl.DataFrame:
        data_base = self.data.copy()
        if add_prefix:
            data_base = {f"{self.source}.{key}": value for key, value in data_base.items()}

        if time_offset is not None:
            data_base["timestamp"] = self.timestamp + time_offset
        else:
            data_base["timestamp"] = self.timestamp

        df = pl.DataFrame(data_base)
        return df

    def __len__(self):
        return 1


@dataclass
class PhysicalDatapacket(GenericDataPacket):
    @dataclass
    class PointDefinition:
        unit: str
        precision: int = 2
        si: bool = True 

        def format(self,value: float) -> str:
            if self.si:
                if value == 0:
                    return f"{0:.{self.precision}f} {self.unit}"    
                if value >= 1e9:
                    return f"{value / 1e9:.{self.precision}f} G{self.unit}"
                elif value >= 1e6:
                    return f"{value / 1e6:.{self.precision}f} M{self.unit}"
                elif value >= 1e3:
                    return f"{value / 1e3:.{self.precision}f} k{self.unit}"
                elif value >= 1:
                    return f"{value:.{self.precision}f} {self.unit}"
                elif value >= 1e-3:
                    return f"{value * 1e3:.{self.precision}f} m{self.unit}"
                elif value >= 1e-6:
                    return f"{value * 1e6:.{self.precision}f} μ{self.unit}"
                else:
                    return f"{value * 1e9:.{self.precision}f} n{self.unit}"
                
            else:
                return f"{value:.{self.precision}f}"
    data: Dict[str, float]  # Contains a single datapoint
    metadata: Dict[str, PointDefinition]

    def get_formatted_data(self) -> Dict[str, str]:
        output = {}
        for key, value in self.data.items():
            if key in self.metadata:
                output[key] = f"{value:.{self.metadata[key].precision}f} {self.metadata[key].unit}"
            else:
                output[key] = str(value)

        return output

    def __str__(self):
        return f"(PhysicalDatapacket) {self.source} - {list(self.data.keys())}"

    def as_flat_dict(self) -> Dict[str, float | str]:
        return {f"{self.source}.{key}": value for key, value in self.data.items()}

    def as_dataframe(self, add_prefix: bool, time_offset: float | None = None) -> pl.DataFrame:
        data_base = self.data.copy()
        if add_prefix:
            data_base = {f"{self.source}.{key}": value for key, value in data_base.items()}

        if time_offset is not None:
            data_base["timestamp"] = self.timestamp + time_offset
        else:
            data_base["timestamp"] = self.timestamp

        df = pl.DataFrame(data_base)
        return df
    
    def get_metadata(self,full_key: str) -> PointDefinition | None:
        item = self.metadata.get(full_key, None)
        if item is not None:
            return item
        
        # Check if the full_key matches the source and metadata key
        for key, value in self.metadata.items():
            if full_key == f"{self.source}.{key}":
                return value
    
        return None
    
        
            
    def __len__(self):
        return 1


# TODO


class ImagePacket: ...


class MultiImagePacket: ...


@dataclass
class MultiPointDataPacket(GenericDataPacket):
    data: pl.DataFrame  # Contains multiple datapoints
    timestamps: pl.Series

    @property
    def dataframe(self) -> pl.DataFrame:
        return self.data.with_columns(pl.lit(self.timestamps).alias("timestamp"))

    @property
    def prefixed_dataframe(self) -> pl.DataFrame:
        data = self.data.rename(lambda column_name: f"{self.source}.{column_name}")
        return data.with_columns(pl.lit(self.timestamps).alias("timestamp"))

    @classmethod
    def from_dataframe(cls, source: str, dataframe: pl.DataFrame) -> "MultiPointDataPacket":
        timestamps = dataframe["timestamp"]
        output_data = dataframe.drop("timestamp")

        return cls(
            timestamp=timestamps[0],
            source=source,
            timestamps=timestamps,
            data=output_data,
        )

    def __len__(self):
        return len(self.timestamps)

    def __str__(self):
        return f"(MultiPointDataPacket) {self.source} - {len(self)} points - {self.data.columns}"

    def as_flat_dict(self) -> Dict[str, float | str]:
        return {f"{self.source}.{key}": value.item() for key, value in self.data.head(1).to_dict().items()}

    def as_dataframe(self, add_prefix: bool, time_offset: float | None = None) -> pl.DataFrame:
        prefixed_dataframe: pl.DataFrame = self.dataframe if not add_prefix else self.prefixed_dataframe

        # relative time
        if time_offset is not None:
            prefixed_dataframe = prefixed_dataframe.with_columns(
                pl.lit(self.timestamps + time_offset).alias("timestamp")
            )
        return prefixed_dataframe
