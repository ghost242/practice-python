from pprint import pprint
from xml.etree import ElementTree

raw_text = """
<root>
    <plant>
        <tree>
            <height>10 ft</height>
            <color>green</color>
            <name>lemon tree</name>
        </tree>
        <grass>
            <height>10 inch</height>
            <color>green</color>
            <name>grass</name>
        </grass>
    </plant>
    <animal>
        <dog>
            <species>puddle</species>
            <height>3 ft</height>
            <name>judy</name>
        </dog>
        <dolphin>
            <species>mammal</species>
            <height>5 ft</height>
            <name>marine</name>
        </dolphin>
        <chicken>
            <species>bird</species>
            <height>10 inch</height>
            <name>foody</name>
        </chicken>
    </animal>
</root>
"""


def sniff(elem):
    master_dict = dict()
    if not elem and elem is not None:
        master_dict[elem.tag] = elem.text

    for child in elem:
        sub_dict = sniff(child)
        if elem.tag not in master_dict:
            master_dict[elem.tag] = sub_dict
        elif isinstance(master_dict[elem.tag], dict):
            master_dict[elem.tag].update(sub_dict)

    return master_dict


if __name__ == "__main__":
    root = ElementTree.fromstring(raw_text)

    res = sniff(root)

    pprint(res, indent=2)
