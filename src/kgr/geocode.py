from argparse import Namespace
from random import uniform
from sys import stderr
from pathlib import Path
from geopy.geocoders import Nominatim
from .lib import read_data, write_data, check_columns


def create_parser(subparsers):
	check_parser = subparsers.add_parser('check', description="Check get geocode for single address")
	check_parser.add_argument("-a", "--address", required=True, help="input address for check")

	geocode_parser = subparsers.add_parser('geocode', description="Get geocode from OpenStreetMap")
	geocode_parser.add_argument("-i", "--input", required=True, help="input csv file with data", type=Path)

	group = geocode_parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-y", "--replace", action="store_true", help="replace input csv file")
	group.add_argument("-o", "--output", help="output csv file", type=Path)

	geocode_parser.add_argument("-r", "--random", action="store_true", help="randomize geocode for exclude collision")
	geocode_parser.add_argument("-d", "--delimiter", help="delimiter in the input csv file", default=",")
	geocode_parser.add_argument("-c", "--encoding", help="encoding of the input csv file", default="UTF-8")
	geocode_parser.add_argument("-v", "--verbosity", action="count", default=0, help="add progress messages")

	group = geocode_parser.add_mutually_exclusive_group()
	group.add_argument("-q", "--quiet", action="store_true", help="ignore get geocode errors")
	group.add_argument("-e", "--error", help="log file for missing persons")

	return subparsers


def get_geocode(city: str, app) -> str:
	location = app.geocode(city)
	assert location, city
	return float(location.raw['lon']), float(location.raw['lat'])


def translate_city_to_geocode(data: list, args: Namespace) -> int:
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
				print(row["ФИО"], file=args.error)
			errors += 1
		finally:
			row["WKT"] = f"""POINT ({row["lon"]} {row["lat"]})"""
			if args.verbosity > 0 and i % 10 == 0 or args.verbosity > 1:
				print(f"Done: {i:>{width}d}/{len(data)}")
	return errors


def check(args: Namespace) -> None:
	"""Request and output the coordinates of the settlement.
	
	The args parameter must contain the string attribute "address"."""
	try:
		print(get_geocode(args.address, Nominatim(user_agent="KGR")))
	except AssertionError:
		print("Error: address not found")


def geocode(args: Namespace) -> None:
	"""Requests the coordinates of the settlements and fills data file.
	
	The source CSV file must contain columns "ФИО" and "city".
	The output CSV file will contain filled columns "lon", "lat" and "WKT"."""
	if args.replace:
		args.output = args.input
	args.error = open(args.error, "w", encoding=args.encoding) if args.error else stderr
	
	data = read_data(args)
	if not data or not check_columns(data[0].keys(), "ФИО", "city"):
		return
	errors = translate_city_to_geocode(data, args)
	if not args.quiet:
		print(f"Не найдено и пропущено адресов: {errors}.")
	write_data(data, headings + ["lon", "lat", "WKT"], args)


