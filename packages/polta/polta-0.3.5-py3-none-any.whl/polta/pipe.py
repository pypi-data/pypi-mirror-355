import polars as pl

from dataclasses import dataclass, field
from datetime import datetime
from polars import DataFrame
from typing import Union
from uuid import uuid4

from polta.enums import LoadLogic, TableQuality
from polta.exceptions import (
  EmptyPipe,
  LoadLogicNotRecognized,
  TableQualityNotRecognized
)
from polta.ingester import PoltaIngester
from polta.table import PoltaTable


@dataclass
class PoltaPipe:
  """Executes data transformation across two layers

  The main methods that should be overriden:
    1. load_dfs() -> populate self.dfs with dependent DataFrames
    2. transform() -> apply transformation logic against self.dfs
  
  The main method that should be executed:
    1. execute() -> executes the pipeline
  
  Args:
    table (PoltaTable): the destination Polta Table
    load_logic (LoadLogic): how the data should be placed in target table
    strict (optional) (bool): indicates whether to fail on empty target DataFrame
  
  Initialized fields:
    dfs (dict[str, DataFrame]): the dependent DataFrames for the pipeline
  """
  table: PoltaTable
  load_logic: LoadLogic
  ingester: Union[PoltaIngester, None] = field(default_factory=lambda: None)
  strict: bool = field(default_factory=lambda: False)
  dfs: dict[str, DataFrame] = field(init=False)

  def __post_init__(self) -> None:
    self.dfs: dict[str, DataFrame] = {}

  def execute(self) -> int:
    """Executes the pipe"""
    self.dfs: dict[str, DataFrame] = self.load_dfs()
    if self.ingester:
      self.dfs['raw'] = self.ingester.ingest()
    df: DataFrame = self.transform()
    df: DataFrame = self.add_metadata_columns(df)
    df: DataFrame = self.conform_schema(df)
    self.save(df)
    return df.shape[0]
  
  def load_dfs(self) -> dict[str, DataFrame]:
    """Loads dependent DataFrames
    
    This should be overriden by a child class
    
    Returns:
      dfs (dict[str, DataFrame]): the dependent DataFrames
    """
    return {}

  def transform(self) -> DataFrame:
    """Transforms the dependent DataFrames into a pre-conformed DataFrame
    
    This should be overriden by a child class

    Returns:
      df (DataFrame): the transformed DataFrame
    """
    if self.ingester:
      return self.dfs['raw']
    return DataFrame([], self.table.schema_polars)

  def add_metadata_columns(self, df: DataFrame) -> DataFrame:
    """Adds relevant metadata columns to the DataFrame before loading

    This method presumes the DataFrame carries its original metadata
    
    Args:
      df (DataFrame): the DataFrame before metadata columns
    
    Returns:
      df (DataFrame): the resulting DataFrame
    """
    id: str = str(uuid4())
    now: datetime = datetime.now()
    
    if self.table.quality.value == TableQuality.RAW.value:
      df: DataFrame = df.with_columns([
        pl.lit(id).alias('_raw_id'),
        pl.lit(now).alias('_ingested_ts')
      ])
    elif self.table.quality.value == TableQuality.CONFORMED.value:
      df: DataFrame = df.with_columns([
        pl.lit(id).alias('_conformed_id'),
        pl.lit(now).alias('_conformed_ts')
      ])
    elif self.table.quality.value == TableQuality.CANONICAL.value:
      df: DataFrame = df.with_columns([
        pl.lit(id).alias('_canonicalized_id'),
        pl.lit(now).alias('_created_ts'),
        pl.lit(now).alias('_modified_ts')
      ])
    else:
      raise TableQualityNotRecognized(self.table.quality.value)

    return df
  
  def conform_schema(self, df: DataFrame) -> DataFrame:
    """Conforms the DataFrame to the expected schema
    
    Args:
      df (DataFrame): the transformed, pre-conformed DataFrame
    
    Returns:
      df (DataFrame): the conformed DataFrame
    """
    df: DataFrame = self.add_metadata_columns(df)
    return df.select(*self.table.schema_polars.keys())

  def save(self, df: DataFrame) -> None:
    """Saves a DataFrame into the target Delta Table
    
    Args:
      df (DataFrame): the DataFrame to load
    """
    print(f'Loading {df.shape[0]} record(s) into {self.table.table_path}')

    if df.is_empty():
      if self.strict:
        raise EmptyPipe()
      return

    if self.load_logic.value == LoadLogic.APPEND.value:
      self.table.append(df)
    elif self.load_logic.value == LoadLogic.OVERWRITE.value:
      self.table.overwrite(df)
    elif self.load_logic.value == LoadLogic.UPSERT.value:
      self.table.upsert(df)
    else:
      raise LoadLogicNotRecognized(self.load_logic)
