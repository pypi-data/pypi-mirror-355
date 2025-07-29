from enum import Enum


class TableQuality(Enum):
  """The quality of the Delta Table"""
  RAW = 'raw'
  CONFORMED = 'conformed'
  CANONICAL = 'canonical'

class LoadLogic(Enum):
  """The method of saving data to a Delta Table"""
  APPEND = 'append'
  OVERWRITE = 'overwrite'
  UPSERT = 'upsert'

class DirectoryType(Enum):
  """Ingestion type"""
  SHALLOW = 'shallow'
  DATED = 'dated'

class RawFileType(Enum):
  """Format of raw files"""
  JSON = 'json'
