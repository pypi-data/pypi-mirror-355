import argparse
from . application import Application



def parse_args():
	parser = argparse.ArgumentParser(prog="Docker", description="Docker automation")
	subparsers = parser.add_subparsers(dest="command")

	stop_parser = subparsers.add_parser("stop", help="Stop containers")
	stop_parser.add_argument("--remove", help="Remove containers after they are stopped", action="store_true")
	stop_parser.add_argument("--image", help="Container image", default=None)

	args = parser.parse_args()
	if args.command is None:
		parser.print_help()
		return

	return args

def main():
	args = parse_args()
	if args is None:
		return

	Application.Run(args)

if __name__ == "__main__":
	main()
