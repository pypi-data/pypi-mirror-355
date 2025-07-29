from dataclasses import dataclass

from polta.pipe import PoltaPipe


@dataclass
class PoltaPipeline:
  """Simple dataclass for executing chains of pipes for an end product"""
  raw_pipes: list[PoltaPipe]
  conformed_pipes: list[PoltaPipe]
  canonical_pipes: list[PoltaPipe]

  def execute(self) -> None:
    """Executes all available pipelines in order of layer"""
    for pipe in self.raw_pipes:
      pipe.execute()
    for pipe in self.conformed_pipes:
      pipe.execute()
    for pipe in self.canonical_pipes:
      pipe.execute()
