import cv2
import numpy as np
import os
from pathlib import Path
import requests

from typing import Union, Literal, Optional


def imread(path: Union[str, Path], flags: int = cv2.IMREAD_COLOR) -> np.ndarray:
    """
    Reads an image from a file, supporting paths with non-ASCII characters.

    Args:
        path (Union[str, Path]): Path to the image file.
        flags (int, optional): Flags specifying the color type of a loaded image.
            Defaults to cv2.IMREAD_COLOR.

    Returns:
        np.ndarray: The loaded image array.
    """
    path = str(path)
    return cv2.imdecode(np.fromfile(path, np.uint8), flags)


def imwrite(
    filename: Union[str, Path],
    img: np.ndarray,
) -> bool:
    """
    Saves an image to a file, supporting paths with non-ASCII characters.

    Args:
        filename (Union[str, Path]): Path to save the image.
        img (np.ndarray): Image data array.


    Returns:
        bool: True if the image is successfully saved, False otherwise.
    """
    filename = str(filename)
    try:
        ext = os.path.splitext(filename)[1]  # file extension with dot, e.g. '.jpg'
        result, encoded_img = cv2.imencode(ext, img)
        if not result:
            return False
        encoded_img.tofile(filename)
        return True
    except Exception:
        return False


def cv_imshow(
    title: str, image: np.ndarray, color_type: Literal["bgr", "rgb"] = "bgr"
) -> None:
    """
    Display an image in a window. Converts color if needed.
    If display fails (e.g., in headless environment), saves the image as a JPEG file.

    Args:
        title (str): Window title or filename prefix if saving.
        image (np.ndarray): Image array.
        color_type (Literal['bgr', 'rgb'], optional): Input image color space.
            Defaults to 'bgr'.

    Returns:
        None
    """
    if color_type == "rgb":
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    try:
        cv2.imshow(title, image)
        cv2.waitKey(0)
        cv2.destroyWindow(title)
    except cv2.error:
        # Fallback: save image if display is not possible
        cv2.imwrite(f"{title}.jpg", image)


def url_to_image(url: str, readFlag: int = cv2.IMREAD_COLOR) -> Optional[np.ndarray]:
    """
    Download an image from a URL and decode it into an OpenCV image.

    Args:
        url (str): URL of the image to download.
        readFlag (int, optional): Flag specifying the color type of a loaded image.
            Defaults to cv2.IMREAD_COLOR.

    Returns:
        Optional[np.ndarray]: Decoded image as a numpy array if successful, else None.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image_array = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(image_array, readFlag)
        return image
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Image decode failed: {e}")
        return None


class Colors:
    """
    Attributes:
        palette (list of tuple): List of RGB color values.
        n (int): The number of colors in the palette.
        pose_palette (np.array): A specific color palette array with dtype np.uint8.
    """

    def __init__(self):
        """Initialize colors as hex = matplotlib.colors.TABLEAU_COLORS.values()."""
        hexs = (
            "FF3838",
            "FF9D97",
            "FF701F",
            "FFB21D",
            "CFD231",
            "48F90A",
            "92CC17",
            "3DDB86",
            "1A9334",
            "00D4BB",
            "2C99A8",
            "00C2FF",
            "344593",
            "6473FF",
            "0018EC",
            "8438FF",
            "520085",
            "CB38FF",
            "FF95C8",
            "FF37C7",
        )
        self.palette = [self.hex2rgb(f"#{c}") for c in hexs]
        self.n = len(self.palette)
        self.pose_palette = np.array(
            [
                [255, 128, 0],
                [255, 153, 51],
                [255, 178, 102],
                [230, 230, 0],
                [255, 153, 255],
                [153, 204, 255],
                [255, 102, 255],
                [255, 51, 255],
                [102, 178, 255],
                [51, 153, 255],
                [255, 153, 153],
                [255, 102, 102],
                [255, 51, 51],
                [153, 255, 153],
                [102, 255, 102],
                [51, 255, 51],
                [0, 255, 0],
                [0, 0, 255],
                [255, 0, 0],
                [255, 255, 255],
            ],
            dtype=np.uint8,
        )

    def __call__(self, i, bgr=False):
        """Converts hex color codes to RGB values."""
        c = self.palette[int(i) % self.n]
        return (c[2], c[1], c[0]) if bgr else c

    @staticmethod
    def hex2rgb(h):
        """Converts hex color codes to RGB values (i.e. default PIL order)."""
        return tuple(int(h[1 + i : 1 + i + 2], 16) for i in (0, 2, 4))
