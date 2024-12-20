from asyncio import Semaphore, run, gather
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pathlib import Path
from .lib import read_data, write_data, check_columns


def create_parser(subparsers):
	prepare_parser = subparsers.add_parser('prepare', description="Parse source csv file from https://memopzk.org")
	prepare_parser.add_argument("-i", "--input", required=True, help="input csv file with data", type=Path)

	group = prepare_parser.add_mutually_exclusive_group(required=True)
	group.add_argument("-y", "--replace", action="store_true", help="replace input csv file")
	group.add_argument("-o", "--output", help="output csv file", type=Path)

	prepare_parser.add_argument("-d", "--delimiter", help="delimiter in the input csv file")
	prepare_parser.add_argument("-c", "--encoding", help="encoding of the input csv file", default="UTF-8")
	prepare_parser.add_argument("-v", "--verbosity", action="count", default=0, help="add progress messages")

	group = prepare_parser.add_mutually_exclusive_group()
	group.add_argument("-q", "--quiet", action="store_true", help="ignore errors")
	group.add_argument("-e", "--error", help="log file for errors")

	return subparsers


async def fetch(url, session, semaphore):
	async with semaphore:
		try:
			async with session.get(url) as response:
				response.raise_for_status()
				return await response.text()
		except Exception as e:
			print(f"Error fetching {url}: {e}")
			return None


def get_description_and_img(html_src: str):
	soup = BeautifulSoup(html_src, 'html.parser')
	description_tag = soup.select_one('div.human-dossier__art > p > p')
	if not description_tag or description_tag.text.strip().startswith("Включение конкретного человека в список"):
		description_tag = soup.select_one('div.human-dossier__art > p')
		assert description_tag
	
	description = description_tag.text.strip().replace("""
""", "").replace("""\r""", " ").replace("  ", " ").replace("  ", " ")
	img = soup.select_one('div.human-dossier-card__img > img').get("src")
	return description, img


async def process_row(row, args, session, semaphore, i, width, total):
	try:
		row["city"] = ""
		html_src = await fetch(row["Полная информация"], session, semaphore)
		if html_src:
			row["description"], row["img_src"] = get_description_and_img(html_src)
		else:
			row["description"], row["img_src"] = "", ""
		if args.verbosity > 0 and i % 10 == 0 or args.verbosity > 1:
			print(f"Done: {i:>{width}d}/{total}")
	except AssertionError:
		row["city"], row["description"], row["img_src"] = "", "", ""
		if not args.quiet:
			print(*row, file=args.error)


async def parse_raw_data(data: list, args):
	width = len(str(len(data)))
	semaphore = Semaphore(10)
	total = len(data)
	async with ClientSession() as session:
		tasks = [process_row(row, args, session, semaphore, i, width, total) for i, row in enumerate(data, 1)]
		await gather(*tasks)


def prepare(args):
	if args.replace:
		args.output = args.input
	data = read_data(args)
	if not data or not check_columns(data[0].keys(), "ФИО", "Полная информация"):
		return
	run(parse_raw_data(data, args))
	write_data(data, args)

