from PIL import Image
from PIL.ExifTags import TAGS


def main():
    """
    {'version': b'GIF89a', 'background': 21, 'transparency': 21, 'duration': 120, 'extension': (b'NETSCAPE2.0', 795), 'loop': 0}
    24
    360 360
    """
    img = Image.open("../../resources/266e9742dc0aa9230e6061710cad3a88.gif")
    exifdata = img.getexif()
    # iterating over all EXIF data fields
    for tag_id in exifdata:
        # get the tag name, instead of human unreadable tag id
        tag = TAGS.get(tag_id, tag_id)
        data = exifdata.get(tag_id)
        # decode bytes
        if isinstance(data, bytes):
            data = data.decode()
        print(f"{tag:25}: {data}")
    print("=" * 32)
    print(img.info)
    # if img.format == "GIF":
    if hasattr(img, "n_frames"):
        print(img.n_frames)
    print(img.width, img.height)


if __name__ == "__main__":
    main()
