from pathlib import Path
import numpy as np
import uvicorn
from imaging_server_kit import algorithm_server, ImageUI, FloatUI, DropDownUI

from ultralytics import YOLO


@algorithm_server(
    title="YOLO Object Detector",
    description="Real-time object detection with YOLO (Ultralytics implementation).",
    algorithm_name="yolo-detect",
    tags=["Deep learning", "YOLO"],
    used_for=["Bounding box detection"],
    parameters={
        "image": ImageUI(title="Image (2D, RGB)", description="Input image."),
        "iou": FloatUI(
            title="IoU",
            description="Intersection over union threshold.",
            min=0,
            max=1.0,
            step=0.1,
            default=0.5,
        ),
        "conf": FloatUI(
            title="Conf.",
            description="Confidence threshold for detection.",
            min=0.0,
            max=1.0,
            step=0.1,
            default=0.5,
        ),
        "device": DropDownUI(
            default="cpu",
            title="Device",
            description="Torch device for inference.",
            items=["cpu", "cuda", "mps"],
        ),
    },
    sample_images=[Path(__file__).parent / "sample_images" / "giraffs.png"],
)
def yolo_detect_server(
    image: np.ndarray,
    iou: float,
    conf: float,
    device: str,
):
    """Run a pretrained YOLO detector model."""

    model = YOLO("yolo11n.pt")

    if image.shape[2] == 4:  # RGBA to RGB
        image = image[..., :3]

    results = model(
        source=image,
        conf=conf,
        iou=iou,
        device=device,
    )

    probabilities = results[0].boxes.conf.cpu().numpy()
    if len(probabilities) == 0:
        return [("Nothing was detected", {}, "text")]

    box_results = results[0].boxes.xyxy.cpu().numpy().reshape((-1, 2, 2))
    classes_indeces = results[0].boxes.cls.cpu().numpy()

    classes = []
    for class_index in classes_indeces:
        classes.append(model.names.get(class_index))

    boxes = []
    for [(x0, y0), (x1, y1)] in box_results:
        boxes.append(
            [
                [x0, y0],
                [x0, y1],
                [x1, y1],
                [x1, y0],
            ]
        )
    boxes = np.array(boxes)
    boxes = boxes[..., ::-1]  # Invert X-Y

    boxes_params = {
        "name": "YOLO detections",
        "face_color": "transparent",
        "opacity": 1.0,
        "edge_width": 1,
        "edge_color": "class",
        "features": {
            "probability": probabilities,
            "class": classes,
        },
    }
    return [
        (boxes, boxes_params, "boxes"),
    ]


if __name__ == "__main__":
    uvicorn.run(yolo_detect_server.app, host="0.0.0.0", port=8000)
