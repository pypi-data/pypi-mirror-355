import polars as pl

from dataclasses import dataclass, field
from datetime import datetime, UTC
from deltalake import Field, Schema
from os import listdir, path
from polars import DataFrame
from polars.datatypes import DataType, List, String, Struct
from uuid import uuid4

from polta.enums import DirectoryType, RawFileType
from polta.exceptions import DirectoryTypeNotRecognized
from polta.maps import PoltaMaps
from polta.table import PoltaTable
from polta.types import RawMetadata
from polta.udfs import file_path_to_json, file_path_to_payload


@dataclass
class PoltaIngester:
  """Dataclass for ingesting files into the target table"""
  table: PoltaTable
  directory_type: DirectoryType
  raw_file_type: RawFileType

  raw_polars_schema: dict[str, DataType] = field(init=False)
  payload_field: Field = field(init=False)
  simple_payload: bool = field(init=False)
  metadata_schema: Schema = field(init=False)
  payload_schema: dict[str, DataType] = field(init=False)

  def __post_init__(self) -> None:
    self.raw_polars_schema: dict[str, DataType] = PoltaMaps \
      .deltalake_schema_to_polars_schema(self.table.raw_schema)
    self.payload_field: Field = Field('payload', 'string')
    self.simple_payload: bool = self.table.raw_schema.fields == [self.payload_field]
    self.metadata_schema: list[Field] = PoltaMaps.QUALITY_TO_METADATA_COLUMNS['raw']
    self.payload_schema: dict[str, DataType] = PoltaMaps.deltalake_schema_to_polars_schema(
      schema=Schema(self.metadata_schema + [self.payload_field])
    )

  def ingest(self) -> DataFrame:
    """Ingests new files into the target table"""
    file_paths: list[str] = self._get_file_paths()
    metadata: list[RawMetadata] = [self._get_file_metadata(p) for p in file_paths]
    df: DataFrame = DataFrame(metadata, schema=self.payload_schema)
    df = self._filter_by_history(df)
    return self._ingest_files(df)

  def _get_file_paths(self) -> list[str]:
    """Retrieves a list of file paths based on ingestion parameters
        
    Returns:
      file_paths (list[str]): the resulting applicable file paths
    """
    if self.directory_type.value == DirectoryType.SHALLOW.value:
      return [
        path.join(self.table.ingestion_zone_path, f)
        for f in listdir(self.table.ingestion_zone_path)
      ]
    elif self.directory_type.value == DirectoryType.DATED.value:
      file_paths: list[str] = []
      for date_str in listdir(self.table.ingestion_zone_path):
        file_paths.extend([
          path.join(self.table.ingestion_zone_path, date_str, f)
          for f in listdir(path.join(self.table.ingestion_zone_path, date_str))
        ])
      return file_paths
    else:
      raise DirectoryTypeNotRecognized(self.directory_type)

  def _filter_by_history(self, file_paths: list[RawMetadata]) -> DataFrame:
    """Removes files from ingestion attempt that have already been ingested
    
    Args:
      file_paths (list[RawMetadata]): the file paths to ingest
    
    Returns:
      file_paths (DataFrame): the resulting DataFrame object with the filtered paths
    """
    paths: DataFrame = DataFrame(file_paths, schema=self.payload_schema)
    hx: DataFrame = (self.table
      .get(select=['_file_path', '_file_mod_ts'], unique=True)
      .group_by('_file_path')
      .agg(pl.col('_file_mod_ts').max())
    )

    return (paths
      .join(hx, '_file_path', 'left')
      .filter(
        (pl.col('_file_mod_ts') > pl.col('_file_mod_ts_right')) |
        (pl.col('_file_mod_ts_right').is_null())
      )
      .drop('_file_mod_ts_right')
    )

  def _ingest_files(self, df: DataFrame) -> DataFrame:
    """Ingests files in the DataFrame according to file type / desired output
    
    Args:
      df (DataFrame): the files to load
    
    Returns:
      df (DataFrame): the ingested files
    """
    if self.simple_payload:
      return self._run_simple_load(df)
    elif self.raw_file_type.value == RawFileType.JSON.value:
      return self._run_json_load(df)
    else:
      raise NotImplementedError(self.raw_file_type)

  def _get_file_metadata(self, file_path: str) -> RawMetadata:
    """Retrieves file metadata from a file

    Args:
      file_path (str): the path to the file
    
    Returns:
      raw_metadata (RawMetadata): the resulting raw metadata of the file
    """
    if not path.exists(file_path):
      raise FileNotFoundError()

    return RawMetadata(
      _raw_id=str(uuid4()),
      _ingested_ts=datetime.now(),
      _file_path=file_path,
      _file_name=path.basename(file_path),
      _file_mod_ts=datetime.fromtimestamp(path.getmtime(file_path), tz=UTC)
    )

  def _run_simple_load(self, df: DataFrame) -> DataFrame:
    """Retrieves the payload from the file path for each row
    
    Args:
      df (DataFrame): the data with metadata to load
    
    Returns:
      df (DataFrame): the resulting DataFrame
    """
    return (df
      .with_columns([
        pl.col('_file_path')
          .map_elements(file_path_to_payload, return_dtype=String)
          .alias('payload')
      ])
    )

  def _run_json_load(self, df: DataFrame) -> DataFrame:
    """Retrieves the payload values from the file path for each row
    
    Args:
      df (DataFrame): the data with metadata to load
    
    Returns:
      df (DataFrame): the resulting DataFrame
    """
    df: DataFrame = (df
      .with_columns([
        pl.col('_file_path')
          .map_elements(
            function=file_path_to_json,
            return_dtype=List(Struct(self.raw_polars_schema))
          )
          .alias('payload')
      ])
      .explode('payload')
      .with_columns([
        pl.col('payload').struct.field(f).alias(f)
        for f in self.raw_polars_schema.keys()
      ])
      .drop('payload')
    )
    return df
