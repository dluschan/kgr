from argparse import ArgumentParser
from csv import DictReader, DictWriter
from random import uniform
from sys import stderr
from xml.dom.minidom import Document

from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from requests import get


def get_description_and_img(src: str):
	soup = BeautifulSoup(get(src).content, 'html.parser')
	description_tag = soup.select_one('div.human-dossier__art > p > p')
	if not description_tag or description_tag.text.strip().startswith("Включение конкретного человека в список"):
		description_tag = soup.select_one('div.human-dossier__art > p')
		assert description_tag
	
	description = description_tag.text.strip().replace("""
""", "").replace("""\r""", " ").replace("  ", " ").replace("  ", " ")
	img = soup.select_one('div.human-dossier-card__img > img').get("src")
	return description, img


def parse_raw_data(data: list, args):
	width = len(str(len(data)))
	for i, row in enumerate(data, 1):
		try:
			row["city"] = ""
			row["description"], row["img_src"] = get_description_and_img(row["Полная информация"])
			if args.verbosity > 0 and i % 10 == 0 or args.verbosity > 1:
				print(f"Done: {i:>{width}d}/{len(data)}")
		except AssertionError:
			row["city"], row["description"], row["img_src"] = "", "", ""
			if not args.quiet:
				print(*row, file=args.error)


def get_geocode(city: str, app) -> str:
	location = app.geocode(f"{city}")
	assert location, city
	return float(location.raw['lon']), float(location.raw['lat'])


def translate_city_to_geocode(data: list, args) -> int:
	app = Nominatim(user_agent="KGR")
	errors = 0
	_MAGIC_SHIFT_ = 0.01
	width = len(str(len(data)))
	for i, row in enumerate(data, 1):
		try:
			row["lon"], row["lat"] = get_geocode(row["city"], app)
			if args.random:
				row["lon"] += round(uniform(-_MAGIC_SHIFT_, _MAGIC_SHIFT_), 7)
				row["lat"] += round(uniform(-_MAGIC_SHIFT_, _MAGIC_SHIFT_), 7)
		except AssertionError:
			row["lon"], row["lat"] = 0, 0
			if not args.quiet:
				print(f"""{row["ФИО"]}""", file=args.error)
			errors += 1
		finally:
			row["WKT"] = f"""POINT ({row["lon"]} {row["lat"]})"""
			if args.verbosity > 0 and i % 10 == 0 or args.verbosity > 1:
				print(f"Done: {i:>{width}d}/{len(data)}")
	return errors


def read_data(args):
	return list(DictReader(open(args.input, newline='', encoding="UTF-8"), delimiter=args.delimiter))


def write_data(data: list, args):
	with open(args.output, 'w', newline='', encoding="UTF-8") as csvfile:
		writer = DictWriter(csvfile, fieldnames=data[0].keys())
		writer.writeheader()
		for row in data:
			writer.writerow(row)


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


def convert_data_to_kml(data: list, args):
	root = Document().createElement("kml")
	root.setAttribute("xmlns", "http://www.opengis.net/kml/2.2")
	doc_tag = Document().createElement("Document")
	name_tag = Document().createElement("name")
	name_tag.appendChild(Document().createTextNode(args.layout))
	doc_tag.appendChild(name_tag)

	for row in data:
		doc_tag.appendChild(create_placemark(row, args.suffix))
	root.appendChild(doc_tag)
	print(root.toprettyxml(), file=open(args.output, "w", encoding="UTF-8"))


def create_parser():
	parser = ArgumentParser(description="Miltitool for convert data from https://memopzk.org to Google Maps")
	subparsers = parser.add_subparsers(dest='command')

	check_parser = subparsers.add_parser('check', description="Check get geocode for single address")
	check_parser.add_argument("-a", "--address", required=True, help="input address for check")

	prepare_parser = subparsers.add_parser('prepare', description="Parse source csv file from https://memopzk.org")
	prepare_parser.add_argument("-i", "--input", required=True, help="input csv file with data")

	group = prepare_parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-y", "--replace", action="store_true", help="replace input csv file")
	group.add_argument("-o", "--output", help="output csv file")

	prepare_parser.add_argument("-d", "--delimiter", help="delimiter for input csv file", default=",")
	prepare_parser.add_argument("-v", "--verbosity", action="count", default=0, help="add progress messages")

	group = prepare_parser.add_mutually_exclusive_group()
	group.add_argument("-q", "--quiet", action="store_true", help="ignore errors")
	group.add_argument("-e", "--error", help="log file for errors")

	geocode_parser = subparsers.add_parser('geocode', description="Get geocode from OpenStreetMap")
	geocode_parser.add_argument("-i", "--input", required=True, help="input csv file with data")

	group = geocode_parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-y", "--replace", action="store_true", help="replace input csv file")
	group.add_argument("-o", "--output", help="output csv file")

	geocode_parser.add_argument("-r", "--random", action="store_true", help="randomize geocode for exclude collision")
	geocode_parser.add_argument("-d", "--delimiter", help="delimiter for input csv file", default=",")
	geocode_parser.add_argument("-v", "--verbosity", action="count", default=0, help="add progress messages")

	group = geocode_parser.add_mutually_exclusive_group()
	group.add_argument("-q", "--quiet", action="store_true", help="ignore get geocode errors")
	group.add_argument("-e", "--error", help="log file for missing persons")

	convert_parser = subparsers.add_parser('convert', description="Convertor data from CSV to KML")
	convert_parser.add_argument("-i", "--input", required=True, help="input csv file with data")
	convert_parser.add_argument("-o", "--output", help="output kml file")
	convert_parser.add_argument("-d", "--delimiter", help="delimiter for input csv file", default=",")
	convert_parser.add_argument("-s", "--suffix", help="the phrase added to the description of each person")
	convert_parser.add_argument("-l", "--layout", help="the internal name of the xml document and the name of the layer on the map")

	return parser


def prepare(args):
	if args.replace:
		args.output = args.input
	data = read_data(args)
	assert len(data), "Empty data"
	assert "ФИО" in data[0].keys(), """Error: Missing column "ФИО"! """
	assert "Полная информация" in data[0].keys(), """Error: Missing column "Полная информация"! """
	parse_raw_data(data, args)
	write_data(data, args)


def geocode(args):
	if args.replace:
		args.output = args.input
	args.error = open(args.error, "w", encoding="UTF-8") if args.error else stderr
	
	data = read_data(args)
	assert len(data), "Empty data"
	assert "ФИО" in data[0].keys(), """Error: Missing column "ФИО"! """
	assert "city" in data[0].keys(), """Error: Missing column "city"! """
	errors = translate_city_to_geocode(data, args)
	if not args.quiet:
		print(f"Не найдено и пропущено адресов: {errors}.")
	
	write_data(data, args)


def convert(args):
	if args.output is None:
		args.output = args.input.replace(".csv", ".kml")
	if args.suffix is None:
		args.suffix = ""
	else:
		args.suffix = " " + args.suffix.strip()
	if args.layout is None:
		args.layout = args.input.replace(".csv", "")
	
	data = read_data(args)
	assert len(data), "Empty data"
	assert "ФИО" in data[0].keys(), """Error: Missing column "ФИО"! """
	assert "img_src" in data[0].keys(), """Error: Missing column "img_src"! """
	assert "description" in data[0].keys(), """Error: Missing column "description"! """
	assert "lon" in data[0].keys(), """Error: Missing column "lon"! """
	assert "lat" in data[0].keys(), """Error: Missing column "lat"! """
	convert_data_to_kml(data, args)


def check(args):
	app = Nominatim(user_agent="KGR")
	try:
		print(get_geocode(args.address, app))
	except AssertionError:
		print("Error: address not found")


def main():
	parser = create_parser()
	args = parser.parse_args()
	match args.command:
		case "check":
			check(args)
		case "prepare":
			prepare(args)
		case "geocode":
			geocode(args)
		case "convert":
			convert(args)
		case _:
			parser.print_help()
