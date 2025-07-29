from dataclasses import dataclass, field
from datetime import datetime
from deltalake import DeltaTable, Field, Schema, TableFeatures
from os import getcwd, makedirs, path
from pathlib import Path
from polars import DataFrame, read_delta
from polars.datatypes import DataType
from shutil import rmtree
from typing import Tuple, Union

from polta.enums import TableQuality
from polta.exceptions import PoltaDataFormatNotRecognized
from polta.maps import PoltaMaps
from polta.metastore import PoltaMetastore
from polta.types import RawPoltaData


@dataclass
class PoltaTable:
  """Class to store all applicable information for a Polars + Delta Table
  
  Positional Args:
    domain (str): the kind of data this table contains
    quality (TableQuality): the quality of the data
    name (str): the name of the table
    
  Optional Args:
    raw_schema (Union[Schema, None]): a deltalake schema (default None)
    metastore (PoltaMetastore): The metastore (default PoltaMetastore())
    primary_keys (list[str]): for upserts, the primary keys of the table (default [])
  
  Initialized fields:
    table_path (str): the absolute path to the Polta Table in the metastore
    state_file_directory (str): the absolute path to the state files directory
    state_file_path (str): the absolute path to the Polta Table state file
    schema_polars (dict[str, DataType]): the table schema as a Polars object
    schema_deltalake (Schema): the table schema as a deltalake object
    columns (list[str]): the table columns
    merge_predicate (str): the SQL merge predicate for upserts
  """
  domain: str
  quality: TableQuality
  name: str
  raw_schema: Union[Schema, None] = field(default_factory=lambda: None)
  metastore: PoltaMetastore = field(default_factory=lambda: PoltaMetastore())
  primary_keys: list[str] = field(default_factory=lambda: [])

  table_path: str = field(init=False)
  ingestion_zone_path: str = field(init=False)
  state_file_directory: str = field(init=False)
  state_file_path: str = field(init=False)
  schema_polars: dict[str, DataType] = field(init=False)
  schema_deltalake: Schema = field(init=False)
  columns: list[str] = field(init=False)
  merge_predicate: str = field(init=False)

  def __post_init__(self) -> None:
    self.table_path: str = path.join(
      self.metastore.tables_directory,
      self.domain,
      self.quality.value,
      self.name
    )
    self.ingestion_zone_path: str = path.join(
      self.metastore.volumes_directory,
      'ingestion',
      self.domain,
      self.name
    )
    self.state_file_directory: str = path.join(
      self.metastore.volumes_directory,
      'state',
      self.domain,
      self.quality.value,
      self.name            
    )
    self.state_file_path: str = path.join(
      self.state_file_directory,
      '.STATE'
    )
    self.schema_deltalake, self.schema_polars = self.build_schemas_from_raw(self.quality, self.raw_schema)
    self.columns: list[str] = list(self.schema_polars.keys())

    if self.primary_keys:
      self.merge_predicate: list[str] = PoltaTable.build_merge_predicate(self.primary_keys)
    if self.quality.value == TableQuality.RAW.value:
      self._build_ingestion_zone_if_not_exists()
    PoltaTable.create_if_not_exists(self.table_path, self.schema_deltalake)

  @staticmethod
  def create_if_not_exists(table_path: str, schema: Schema) -> None:
    """Creates a Delta Table if it does not exist

    Args:
        table_path (str): the path of the Delta Table
        schema (Schema): the table schema, in case the Delta Table needs to be created
    """
    if not isinstance(table_path, str):
      raise TypeError('Error: table_path must be of type <str>')
    if not isinstance(schema, Schema):
      raise TypeError('Error: schema must be of type <Schema>')

    # If the Delta Table does not exist yet, create it with the expected schema             
    if not DeltaTable.is_deltatable(table_path):
      makedirs(table_path, exist_ok=True)

    dt: DeltaTable = DeltaTable.create(table_path, schema, mode='ignore')
    dt.alter.add_feature(
      feature=TableFeatures.TimestampWithoutTimezone,
      allow_protocol_versions_increase=True
    )   

  @staticmethod
  def build_schemas_from_raw(quality: TableQuality, raw_schema: Union[Schema, None]) -> \
                        Tuple[Schema, dict[str, DataType]]:
    """Takes a raw deltalake schema and populates deltalake and polars schemas from it
    
    Args:
      quality (TableQuality): the quality of the table, to decide proper metadata
      raw_schema (Union[Schema, None]): the raw schema, if applicable
    
    Returns:
      deltalake_schema, polars_schema (Tuple[Schema, dict[str, DataType]]): the resulting schemas
    """
    metadata_schema: Schema = PoltaMaps.QUALITY_TO_METADATA_COLUMNS[quality.value]
    fields: list[Field] = metadata_schema + (raw_schema.fields if raw_schema is not None else [])
    dl_schema: Schema = Schema(fields)
    return dl_schema, PoltaMaps.deltalake_schema_to_polars_schema(dl_schema)

  @staticmethod
  def build_merge_predicate(primary_keys: list[str]) -> str:
    """Constructs a merge predicate based on the source/target aliases and primary keys

    Args:
      primary_keys (list[str]): the primary keys for the merge

    Returns:
      merge_predicate (str): the merge predicate as a conjunction of SQL conditions matching on primary keys
    """
    return ' AND '.join([f's.{k} = t.{k}' for k in primary_keys])

  def enforce_dataframe(self, data: Union[DataFrame, dict, list[dict]]) -> DataFrame:
    """Takes either a DataFrame or record(s) and returns the DataFrame representation
    
    Args:
      data (Union[DataFrame, dict]): the data to enforce
    
    Returns:
      df (DataFrame): the DataFrame representation
    """
    if isinstance(data, dict):
      return DataFrame([data], self.schema_polars)
    elif isinstance(data, list) and all(isinstance(r, dict) for r in data):
      return DataFrame(data, self.schema_polars)
    elif isinstance(data, DataFrame):
      return data
    else:
      raise PoltaDataFormatNotRecognized(type(data))

  def truncate(self) -> None:
    """Truncates the table"""
    self.overwrite(DataFrame([], self.schema_polars))

  def drop(self) -> None:
    """Drops the table"""
    if path.exists(self.table_path) and DeltaTable.is_deltatable(self.table_path):
      rmtree(self.table_path)
    
  def get_as_delta_table(self) -> DeltaTable:
    """Retrieves the DeltaTable object for the Polta Table
    
    Returns:
      delta_table (DeltaTable): the resulting Delta Table
    """
    self.create_if_not_exists(self.table_path, self.schema_deltalake)
    return DeltaTable(self.table_path)

  def get(self, filter_conditions: dict = {}, partition_by: list[str] = [], order_by: list[str] = [],
          order_by_descending: bool = True, select: list[str] = [], sort_by: list[str] = [], limit: int = 0,
          unique: bool = False) -> DataFrame:
    """Retrieves a record, or records, by a specific condition, expecting only one record to return
      
    Args:
      filter_conditions (optional) (dict): if applicable, the filter conditions (e.g., {file_path: 'path.json'})
      partition_by (optional) (list[str]): if applicable, the keys by which to partition during deduplication
      order_by (optional) (list[str]): if applicable, the columns by which to order during deduplication
      order_by_descending (optional) (bool): if applicable, whether to ORDER BY DESC
      select (optional) (list[str]): if applicable, the columns to return after retrieving the DataFrame
      sort_by (optional) (list[str]): if applicable, the columns by which to sort the output
      limit (optional) (int): if applicable, a limit to the number of rows to return
      unique (optional) (bool): if applicable, remove any duplicate records

    Returns:
      df (DataFrame): the resulting DataFrame
    """
    if not isinstance(filter_conditions, dict):
      raise TypeError('Error: filter_conditions must be of type <dict>')
    if not isinstance(partition_by, list):
      raise TypeError('Error: partition_by must be of type <list>')
    if not isinstance(order_by, list):
      raise TypeError('Error: order_by must be of type <list>')
    if not isinstance(select, list):
      raise TypeError('Error: select must be of type <list>')
    if not isinstance(sort_by, list):
      raise TypeError('Error: sort_by must be of type <list>')
    if not isinstance(limit, int):
      raise TypeError('Error: limit must be of type <int>')
    if not isinstance(unique, bool):
      raise TypeError('Error: unique must be of type <bool>')
    if not all(isinstance(c, str) for c in partition_by):
      raise ValueError('Error: all values in partition_by must be of type <str>')
    if not all(isinstance(c, str) for c in order_by):
      raise ValueError('Error: all values in order_by must be of type <str>')
    if not all(isinstance(c, str) for c in select):
      raise ValueError('Error: all values in select must be of type <str>')
    if not all(isinstance(c, str) for c in sort_by):
      raise ValueError('Error: all values in sort_by must be of type <str>')

    # Create the Delta Table if it does not exist
    if not path.exists(self.table_path):
      self.create_if_not_exists(self.table_path, self.schema_deltalake)
        
    # Retrieve Delta Table as a Polars DataFrame
    df: DataFrame = read_delta(self.table_path)

    # Apply the filter condition if applicable
    if filter_conditions:
      df: DataFrame = df.filter(**filter_conditions)

    # Filter columns if applicable
    if select:
      df: DataFrame = df.select(select)

    # Apply a simple deduplication if applicable        
    if partition_by and order_by:
      df: DataFrame = df \
        .sort(order_by, descending=order_by_descending) \
        .unique(subset=partition_by, keep='first')
    
    # Apply a limit if applicable
    if limit:
      df: DataFrame = df.limit(limit)
    
    # Remove duplicate records if applicable
    if unique:
      df: DataFrame = df.unique()
      
    # Sort the results if applicable
    if sort_by:
      df: DataFrame = df.sort(sort_by)

    return df
  
  def upsert(self, data: RawPoltaData) -> None:
    """Upserts a DataFrame into the Delta Table

    self.primary_keys must be specified for this method to run
    
    Args:
      data (RawPoltaData): the data to upsert
    """
    if not self.primary_keys:
      raise ValueError('Error: Delta Table does not have primary keys')
    if not self.merge_predicate:
      raise ValueError('Error: merge predicate did not initialize')

    # Ensure DataFrame type
    df: DataFrame = self.enforce_dataframe(data)

    # Merge the DataFrame into its respective Delta Table
    # This merge logic is a simple upsert based on the table's primary keys
    (df
      .write_delta(
        target=self.table_path,
        mode='merge',
        delta_merge_options={
          'predicate': self.merge_predicate,
          'source_alias': 's',
          'target_alias': 't',
        }
      )
      .when_matched_update_all()
      .when_not_matched_insert_all()
      .execute()
    )
    self.touch_state_file()

  def overwrite(self, data: RawPoltaData) -> None:
    """Overwrites the Delta Table with the inputted DataFrame
    
    Args:
      data (RawPoltaData): the data with which to overwrite
    """
    # Ensure DataFrame type
    df: DataFrame = self.enforce_dataframe(data)

    df.write_delta(
      target=self.table_path,
      mode='overwrite'
    )      
    self.touch_state_file()

  def append(self, data: RawPoltaData) -> None:
    """Appends a DataFrame to the Delta Table

    Args:
      data (RawPoltaData): the data with which to append
    """    
    # Ensure DataFrame type
    df: DataFrame = self.enforce_dataframe(data)

    df.write_delta(
      target=self.table_path,
      mode='append'
    )
    self.touch_state_file()

  def touch_state_file(self) -> None:
    """Touches the state file to update the last modified datetime"""
    try:
      Path(self.state_file_path).touch()
    except FileNotFoundError:
      makedirs(self.state_file_directory, exist_ok=True)        
      Path(self.state_file_path).touch()

  def get_last_modified_datetime(self) -> datetime:
    """Retrieves the last modified datetime of the table
    
    Returns:
      last_modified_datetime (datetime): the last modified datetime of the table
    """
    modified_time: float = path.getmtime(self.state_file_path)
    return datetime.fromtimestamp(modified_time)

  def get_last_modified_record(self) -> dict[str, any]:
    """Builds a dict record for last modified information

    Returns:
      last_modified_record (dict[str, any]): the metadata of the table's last modified timestamp
    """
    return {
      'domain': self.domain,
      'quality': self.quality.value,
      'table': self.name,
      'path': self.table_path,
      'last_modified_datetime': self.get_last_modified_datetime()
    }

  def _build_ingestion_zone_if_not_exists(self) -> None:
    """Builds an empty directory for ingesting files"""
    if not path.exists(self.ingestion_zone_path):
      makedirs(self.ingestion_zone_path, exist_ok=True)
      print(f'Ingestion zone created: {self.ingestion_zone_path}')
