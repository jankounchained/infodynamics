__version__ = "0.1.0"

from infodynamics.clustering import SignalClusterer
from infodynamics.text.morphology import MorphologicalEncoder
from infodynamics.pipeline import InfoDynamics, MultiscaleInfoDynamics
from infodynamics.scalogram import FooteNovelty, Scalogram, self_similarity_matrix, structure_descriptors
from infodynamics.text.segmentation import Chunk, segment, strip_markdown
from infodynamics.time_series import WindowedRollingDistance
