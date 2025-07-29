from typing import Iterator, Annotated, Optional, Tuple
import numpy

def camera_dimensions(aspect_ratio: float) -> Tuple[float, float]:
    ...
def max_camera_dimensions() -> Tuple[float, float]:
    ...

from typing import Iterator, Literal

class Map:
    info: Info
    groups: Groups
    images: Images
    envelopes: Envelopes
    def __init__(self, path):
        ...
    @staticmethod
    def empty(version: str) -> Map:
        ...
    def save(self, path: str):
        ...
    def save_dir(self, path: str):
        ...
    def embed_images(self, mapres_directory: Optional[str] = None):
        ...
    def rotate(self):
        ...
    def mirror(self):
        ...
    def version(self) -> Literal['DDNet06', 'Teeworlds07']:
        ...
    def physics_group(self) -> Optional[Group]:
        ...
    def game_layer(self) -> Optional[Layer]:
        ...
    def front_layer(self) -> Optional[Layer]:
        ...
    def tele_layer(self) -> Optional[Layer]:
        ...
    def speedup_layer(self) -> Optional[Layer]:
        ...
    def switch_layer(self) -> Optional[Layer]:
        ...
    def tune_layer(self) -> Optional[Layer]:
        ...

class Info:
    author: str
    version: str
    credits: str
    license: str
    settings: list[str]

class Images:
    def new_from_file(self, path: str) -> Image:
        ...
    def new_external(self, name: str) -> Image:
        ...
    def new_from_teeworlds(self, name: str) -> Image:
        ...
    def new_from_ddnet(self, name: str) -> Image:
        ...
    def new_from_data(self, name: str, py_array3: numpy.ndarray) -> Image:
        ...
    def __iter__(self) -> Iterator[Image]:
        ...
    def __next__(self) -> Image:
        ...
    def __getitem__(self, index: int) -> Image:
        ...

class Image:
    name: str
    data: Optional[numpy.ndarray]
    def width(self) -> int:
        ...
    def height(self) -> int:
        ...
    def is_external(self) -> bool:
        ...
    def is_embedded(self) -> bool:
        ...
    def save(self, path: str):
        ...
    def embed(self, path: str):
        ...

class Groups:
    def new(self) -> Group:
        ...
    def new_physics(self) -> Group:
        ...
    def __iter__(self) -> Iterator[Group]:
        ...
    def __next__(self) -> Group:
        ...
    def __getitem__(self, index: int) -> Group:
        ...

class Group:
    name: str
    layers: Layers
    offset_x: float
    offset_y: float
    parallax_x: float
    parallax_y: float
    clipping: bool
    clip_x: float
    clip_y: float
    clip_width: float
    clip_height: float
    def is_physics_group(self) -> bool:
        ...

class Layers:
    def new_quads(self) -> Layer:
        ...
    def new_sounds(self) -> Layer:
        ...
    def new_tiles(self, width: int, height: int) -> Layer:
        ...
    def new_game(self, width: int, height: int) -> Layer:
        ...
    def new_physics(self, kind: Literal['Game', 'Front', 'Tele', 'Speedup', 'Switch', 'Tune']) -> Layer:
        ...
    def __iter__(self) -> Iterator[Layer]:
        ...
    def __next__(self) -> Layer:
        ...
    def __getitem__(self, index: int) -> Layer:
        ...

class Layer:
    tiles: numpy.ndarray
    image: Optional[int]
    quads: Quads
    color: Tuple[int, int, int, int]
    name: str
    def width(self) -> int:
        ...
    def height(self) -> int:
        ...
    def kind(self) -> Literal['Tiles', 'Quads', 'Sounds', 'Game', 'Front', 'Tele', 'Speedup', 'Switch', 'Tune']:
        ...
    def to_mesh(self) -> tuple:
        ...

class Quads:
    def new(self, pos_x: float, pos_y: float, width: float, height: float) -> Quad:
        ...
    def __iter__(self) -> Iterator[Quad]:
        ...
    def __next__(self) -> Quad:
        ...
    def __getitem__(self, index: int) -> Quad:
        ...

class Quad:
    position: Tuple[float, float]
    corners: list
    colors: Annotated[list[int], 4]
    texture_coords: Annotated[list[Tuple[float, float]], 4]
    position_env: Optional[int]
    position_env_offset: int
    color_env: Optional[int]
    color_env_offset: int


class Envelopes:
    def new(self, kind: Literal['Position', 'Color', 'Sound']) -> Envelope:
        ...
    def __len__(self) -> int:
        ...
    def __iter__(self) -> Iterator[Envelope]:
        ...
    def __next__(self) -> Envelope:
        ...
    def __getitem__(self, index: int) -> Envelope:
        ...

class Envelope:
    name: str
    points: EnvPoints
    def kind(self) -> Literal['Position', 'Color', 'Sound']:
        ...

class EnvPoints:
    def new(self, time: int) -> EnvPoint:
        ...
    def __iter__(self) -> Iterator[EnvPoint]:
        ...
    def __next__(self) -> EnvPoint:
        ...
    def __getitem__(self, index: int) -> EnvPoint:
        ...

class EnvPoint:
    time: int
    curve: Literal['Step', 'Linear', 'Slow', 'Fast', 'Smooth', 'Bezier']

    # pos
    x: float
    y: float

    # color
    r: float
    g: float
    b: float
    a: float

    # different shape for color and pos points
    content: tuple
