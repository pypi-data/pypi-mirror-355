from typing import List, Tuple
from pathlib import Path
import numpy as np
import uvicorn
import rembg
from imaging_server_kit import algorithm_server, ImageUI, DropDownUI


sessions: dict[str, rembg.sessions.BaseSession] = {}


@algorithm_server(
    algorithm_name="rembg",
    parameters={
        "image": ImageUI(
            title="Image",
            description="Input image (2D grayscale, RGB)",
            dimensionality=[2, 3],
        ),
        "rembg_model_name": DropDownUI(
            default="silueta",
            title="Model",
            description="The model used for background removal.",
            items=["silueta", "u2net"],
        ),
    },
    sample_images=[
        str(Path(__file__).parent / "sample_images" / "astronaut.tif"),
    ],
    title="Rembg",
    description="A tool to remove images background.",
    used_for=["Segmentation"],
    tags=["Deep learning"],
    project_url="https://github.com/danielgatis/rembg",
)
def rembg_server(
    image: np.ndarray,
    rembg_model_name: str = "silueta",
) -> List[Tuple]:
    """Binary segmentation using rembg."""

    session = sessions.setdefault(rembg_model_name, rembg.new_session(rembg_model_name))

    segmentation = rembg.remove(
        data=image,
        session=session,
        only_mask=True,
        post_process_mask=True,
    )
    segmentation = segmentation == 255

    return [(segmentation, {"name": f"{rembg_model_name}_result"}, "mask")]


if __name__ == "__main__":
    uvicorn.run(rembg_server.app, host="0.0.0.0", port=8000)
