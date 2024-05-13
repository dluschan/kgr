from argparse import Namespace
from xml.dom.minidom import Document
from pathlib import Path
from .lib import read_data, check_columns


def create_parser(subparsers):
	convert_parser = subparsers.add_parser('convert', description="Convertor data from CSV to KML")
	convert_parser.add_argument("-i", "--input", required=True, help="input csv file with data", type=Path)
	convert_parser.add_argument("-o", "--output", help="output kml file", type=Path)
	convert_parser.add_argument("-d", "--delimiter", help="delimiter in the input csv file", default=",")
	convert_parser.add_argument("-c", "--encoding", help="encoding of the input csv file", default="UTF-8")
	convert_parser.add_argument("-s", "--suffix", help="the phrase added to the description of each person")
	convert_parser.add_argument("-l", "--layout", help="the internal name of the xml document and the name of the layer on the map")
	return subparsers


def create_placemark(row: dict, src_name: str):
	placemark_tag = Document().createElement("Placemark")

	name_tag = Document().createElement("name")
	name_tag.appendChild(Document().createTextNode(row["ФИО"]))
	placemark_tag.appendChild(name_tag)

	img_tag = Document().createElement("img")
	img_tag.setAttribute("src", row["img_src"])
	img_tag.setAttribute("alt", f"""Фотография: {row["ФИО"]}""")
	p_tag = Document().createElement("p")
	p_tag.appendChild(Document().createTextNode(row["description"] + src_name))
	description_tag = Document().createElement("description")
	description_tag.appendChild(Document().createCDATASection(img_tag.toprettyxml() + p_tag.toprettyxml()))
	placemark_tag.appendChild(description_tag)

	point_tag = Document().createElement("Point")
	coordinates_tag = Document().createElement("coordinates")
	coordinates_tag.appendChild(Document().createTextNode(f"{row['lon']}, {row['lat']}, 0"))
	point_tag.appendChild(coordinates_tag)
	placemark_tag.appendChild(point_tag)
	
	return placemark_tag


def convert_data_to_kml(data: list, layout: str, suffix: str) -> Document:
	root = Document().createElement("kml")
	root.setAttribute("xmlns", "http://www.opengis.net/kml/2.2")
	doc_tag = Document().createElement("Document")
	name_tag = Document().createElement("name")
	name_tag.appendChild(Document().createTextNode(layout))
	doc_tag.appendChild(name_tag)

	for row in data:
		doc_tag.appendChild(create_placemark(row, suffix))
	root.appendChild(doc_tag)
	return root


def convert(args: Namespace) -> None:
	"""Convert a datafile from CSV to KML format.
	
	The source file must contain columns "ФИО", "description", img_src", "lon", and "lat"."""
	if args.output is None:
		args.output = args.input.with_suffix(".kml")
	if args.suffix is None:
		args.suffix = ""
	else:
		args.suffix = " " + args.suffix.strip()
	if args.layout is None:
		args.layout = args.input.stem
	
	data = read_data(args)
	if not data or not check_columns(data[0].keys(), "ФИО", "img_src", "description", "lon", "lat"):
		return
	print(convert_data_to_kml(data, args.layout, args.suffix).toprettyxml(), file=open(args.output, "w", encoding=args.encoding))


