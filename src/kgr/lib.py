from collections.abc import Iterable, Mapping
from argparse import ArgumentParser, Namespace
from csv import DictReader, DictWriter, Sniffer
from importlib.metadata import version


def read_data(args: Namespace) -> Iterable[Mapping]:
	with open(args.input, newline='', encoding=args.encoding) as csvfile:
		if args.delimiter is None:
			dialect = Sniffer().sniff(csvfile.read(1024))
			csvfile.seek(0)
			args.delimiter = dialect.delimiter
		return list(DictReader(csvfile, delimiter=args.delimiter))


def write_data(data: Iterable[Mapping], args: Namespace) -> None:
	with open(args.output, 'w', newline='', encoding=args.encoding) as csvfile:
		writer = DictWriter(csvfile, fieldnames=data[0].keys())
		writer.writeheader()
		for row in data:
			writer.writerow(row)


def check_columns(headings: Iterable[str], *col_names) -> bool:
	for col_name in col_names:
		if col_name not in headings:
			print(f"""Error: Missing column "{col_name}"!""")
			print(f"Found columns: {headings}")
			print("Check used CSV delimiter!")
			return False
	return True


def create_parser() -> ArgumentParser:
	parser = ArgumentParser(description="Miltitool for convert data from https://memopzk.org to Google Maps")
	parser.add_argument("-v", "--version", action='version', version=version("kgr"))
	return parser


