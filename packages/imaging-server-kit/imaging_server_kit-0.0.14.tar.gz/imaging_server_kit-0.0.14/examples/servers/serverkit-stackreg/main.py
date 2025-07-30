from typing import List
from pathlib import Path
import numpy as np
import uvicorn
from pystackreg import StackReg

from imaging_server_kit import algorithm_server, ImageUI, DropDownUI, IntUI


reg_type_dict = {
    "affine": StackReg.AFFINE,
    "rigid": StackReg.RIGID_BODY,
}


@algorithm_server(
    title="pyStackReg",
    description="Register one or more images to a common reference image.",
    algorithm_name="pystackreg",
    project_url=
    parameters={
        "image_stack": ImageUI(
            title="Image stack",
            description="2D image stack in (T)ZYX order.",
            dimensionality=[3],
        ),
        "reg_type": DropDownUI(
            title="Type",
            description="Registration type.",
            items=list(reg_type_dict.keys()),
            default="rigid",
        ),
        "reference": DropDownUI(
            title="Reference",
            description="Reference for the registration",
            items=["previous", "first", "mean"],
            default="previous",
        ),
        "axis": IntUI(
            title="Axis",
            description="Registration axis.",
            default=0,
            min=0,
            max=2,
        ),
    },
    sample_images=[Path(__file__).parent / "sample_images" / "pc12-unreg.tif"],
)
def stackreg_server(
    image_stack: np.ndarray,
    reg_type: str,
    reference: str,
    axis: int,
) -> List[tuple]:
    """Run the Pystackreg algorithm."""
    sr = StackReg(reg_type_dict.get(reg_type))
    tmats = sr.register_stack(image_stack, reference=reference, axis=axis)
    registered_stack = sr.transform_stack(image_stack, tmats=tmats)
    return [(registered_stack, {"name": "Registered stack"}, "image")]


if __name__ == "__main__":
    uvicorn.run(stackreg_server.app, host="0.0.0.0", port=8000)
