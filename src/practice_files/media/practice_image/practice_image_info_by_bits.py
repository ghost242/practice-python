from array import array


def main():
    """
    SOS array('B', [255, 218, 0, 12, 3, 0, 0, 1, 17, 2, 17, 0, 63, 0])
    length of segment depends on the number of components:  array('B', [0, 12])
    number of components (1=monochrome, 3=colour):  3
    0x01 = Y, 0x00 = Huffman table to use:  array('B', [0, 0])
    0x02 = Cb, 0x11 = Huffman table to use:  array('B', [1, 17])
    0x03 = Cr, 0x11 = Huffman table to use:  array('B', [2, 17])
    start of spectral selection or predictor selection 0
    end of spectral selection 63
    successive approximation bit position or point transform 0
    SOF array('B', [255, 192, 0, 17, 8, 5, 85, 8, 0, 3, 0, 17, 0, 1, 17, 1, 2, 17, 1])
    SOF0 segement:  array('B', [255, 192])
    length of segment depends on the number of components:  array('B', [0, 17])
    bits per pixel:  8
    image height:  array('B', [5, 85])
    image width:  array('B', [8, 0])
    number of components (should be 1 or 3):  3
    0x01=Y component, 0x22=sampling factor, quantization table number:  array('B', [0, 17, 0])
    0x02=Cb component, ...:  array('B', [1, 17, 1])
    0x03=Cr component, ...:  array('B', [2, 17, 1])
    """
    with open("../../resources/35163667010_8bfcaef274_k.jpg", "rb") as fd:
        content = array("B", fd.read())
        v_content = memoryview(content)
        start_of_scan = [0xFF, 0xDA]
        start_of_frame = [0xFF, 0xC0]
        eof = [0xFF, 0xD9]
        meta_scan_info = None
        meta_frame_info = None
        body = None
        body_idx = 0

        for idx in range(0, len(v_content) - 2):
            if [v_content[idx], v_content[idx + 1]] == start_of_frame:
                meta_frame_info = array("B", v_content[idx : idx + 19])
            if [v_content[idx], v_content[idx + 1]] == start_of_scan:
                meta_scan_info = array("B", v_content[idx : idx + 14])
                body = array("B", v_content[idx + 14 :])
                break

        # if [body[-2], body[-1]] != eof:
        #     raise Exception("File not has valid end of file")
        print("SOS", meta_scan_info)
        print(
            "length of segment depends on the number of components: ",
            meta_scan_info[2:4],
        )
        print(
            "number of components (1=monochrome, 3=colour): ",
            meta_scan_info[4],
        )
        print("0x01 = Y, 0x00 = Huffman table to use: ", meta_scan_info[5:7])
        print("0x02 = Cb, 0x11 = Huffman table to use: ", meta_scan_info[7:9])
        print("0x03 = Cr, 0x11 = Huffman table to use: ", meta_scan_info[9:11])
        print(
            "start of spectral selection or predictor selection",
            meta_scan_info[11],
        )
        print("end of spectral selection", meta_scan_info[12])
        print(
            "successive approximation bit position or point transform",
            meta_scan_info[13],
        )

        print("SOF", meta_frame_info)
        print("SOF0 segement: ", meta_frame_info[0:2])
        print(
            "length of segment depends on the number of components: ",
            meta_frame_info[2:4],
        )
        print("bits per pixel: ", meta_frame_info[4])
        print("image height: ", meta_frame_info[5:7])
        print("image width: ", meta_frame_info[7:9])
        print("number of components (should be 1 or 3): ", meta_frame_info[9])
        print(
            "0x01=Y component, 0x22=sampling factor, quantization table number: ",
            meta_frame_info[10:13],
        )
        print("0x02=Cb component, ...: ", meta_frame_info[13:16])
        print("0x03=Cr component, ...: ", meta_frame_info[16:19])


if __name__ == "__main__":
    main()
