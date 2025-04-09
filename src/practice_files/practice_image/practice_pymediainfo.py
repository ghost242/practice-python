import json
from pprint import pprint

from pymediainfo import MediaInfo


def main():
    """
    {'tracks': [{'codecs_image': 'GIF',
                 'commercial_name': 'GIF',
                 'complete_name': '../../resources/266e9742dc0aa9230e6061710cad3a88.gif',
                 'count': '331',
                 'count_of_image_streams': '1',
                 'count_of_stream_of_this_kind': '1',
                 'file_extension': 'gif',
                 'file_last_modification_date': 'UTC 2020-05-29 02:44:01',
                 'file_last_modification_date__local': '2020-05-29 11:44:01',
                 'file_name': '266e9742dc0aa9230e6061710cad3a88',
                 'file_name_extension': '266e9742dc0aa9230e6061710cad3a88.gif',
                 'file_size': 181078,
                 'folder_name': '../../resources',
                 'format': 'GIF',
                 'format_extensions_usually_used': 'gif gis',
                 'format_info': 'Graphics Interchange Format',
                 'image_format_list': 'GIF',
                 'image_format_withhint_list': 'GIF',
                 'internet_media_type': 'image/gif',
                 'kind_of_stream': 'General',
                 'other_file_size': ['177 KiB',
                                     '177 KiB',
                                     '177 KiB',
                                     '177 KiB',
                                     '176.8 KiB'],
                 'other_format': ['GIF'],
                 'other_kind_of_stream': ['General'],
                 'stream_identifier': '0',
                 'track_type': 'General'},
                {'commercial_name': 'GIF',
                 'compression_mode': 'Lossless',
                 'count': '124',
                 'count_of_stream_of_this_kind': '1',
                 'format': 'GIF',
                 'format_info': 'Graphics Interchange Format',
                 'format_profile': '89a',
                 'height': 360,
                 'internet_media_type': 'image/gif',
                 'kind_of_stream': 'Image',
                 'other_compression_mode': ['Lossless'],
                 'other_format': ['GIF'],
                 'other_height': ['360 pixels'],
                 'other_kind_of_stream': ['Image'],
                 'other_width': ['360 pixels'],
                 'stream_identifier': '0',
                 'track_type': 'Image',
                 'width': 360}]}
    """
    info = MediaInfo.parse("../../resources/35163667010_8bfcaef274_k.jpg")

    attrs = dir(info)

    for k in attrs:
        if k.startswith("_"):
            continue
        print(f"{k}: {getattr(info, k)}")
    pprint(json.loads(info.to_json()))


if __name__ == "__main__":
    main()
