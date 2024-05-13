from .convert import convert, create_parser as create_convert_parser
from .geocode import geocode, check, create_parser as create_geocode_parser
from .prepare import prepare, create_parser as create_prepare_parser
from .lib import create_parser


def main():
	parser = create_parser()
	subparsers = parser.add_subparsers(dest='command')
	create_prepare_parser(create_geocode_parser(create_convert_parser(subparsers)))
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


main()
