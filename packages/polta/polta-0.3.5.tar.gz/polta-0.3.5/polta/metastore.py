from dataclasses import dataclass, field
from os import getcwd, listdir, makedirs, path

from polta.enums import TableQuality
from polta.exceptions import DomainDoesNotExist


@dataclass
class PoltaMetastore:
  """Dataclass for managing Polta metastores"""
  main_path: str = field(default_factory=lambda: path.join(getcwd(), 'metastore'))
  tables_directory: str = field(init=False)
  volumes_directory: str = field(init=False)

  def __post_init__(self) -> None:
    self.tables_directory: str = path.join(self.main_path, 'tables')
    self.volumes_directory: str = path.join(self.main_path, 'volumes')
    self.initialize_if_not_exists()

  def initialize_if_not_exists(self) -> None:
    """Initializes the metastore if it does not exist"""
    if path.exists(self.main_path):
      return

    makedirs(self.main_path, exist_ok=True)
    makedirs(self.tables_directory, exist_ok=True)
    makedirs(self.volumes_directory, exist_ok=True)

  def list_domains(self) -> list[str]:
    """Retrieves the directories and names of available domains
    
    Returns:
      domains (list[str]): the available qualities
    """
    return listdir(self.tables_directory)

  def list_qualities(self, domain: str) -> list[TableQuality]:
    """Retrieves the available table qualities for a domain
    
    Args:
      domain (str): the domain to check
    
    Returns:
      qualities (list[TableQuality]): the available qualities for that domain
    """
    qualities_path: str = path.join(self.tables_directory, domain)
    if not path.exists(qualities_path):
      raise DomainDoesNotExist(domain)
    return [TableQuality(q) for q in listdir(qualities_path)]

  def domain_exists(self, domain: str) -> bool:
    """Indicates whether the domain exists
    
    Args:
      domain (str): the domain to check
    
    Returns:
      domain_exists (bool): indicates whether the domain exists
    """
    return path.exists(path.join(self.tables_directory, domain))

  def quality_exists(self, domain: str, quality: TableQuality) -> bool:
    """Indicates whether the quality exists under a given domain
    
    Args:
      domain (str): the domain containing the quality to check
      quality (TableQuality): the quality to check
    
    Returns:
      quality_exists (bool): indicates whether the quality exists
    """
    return path.exists(path.join(self.tables_directory, domain, quality.value))
