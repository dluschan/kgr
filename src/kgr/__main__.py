from .convert import convert, create_parser as create_convert_parser
from .geocode import geocode, check, create_parser as create_geocode_parser
from .prepare import prepare, create_parser as create_prepare_parser
from .lib import create_parser


def main():
	parser = create_parser()
	subparsers = parser.add_subparsers(dest='command')
	create_prepare_parser(create_geocode_parser(create_convert_parser(subparsers)))
	args = parser.parse_args()
	commands = {"check": check, "prepare": prepare, "geocode": geocode, "convert": convert}
	if args.command not in commands:
		parser.print_help()
	else:
		commands[args.command](args)


main()
