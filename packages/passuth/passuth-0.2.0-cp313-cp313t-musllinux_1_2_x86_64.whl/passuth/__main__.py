import argparse

from passuth import generate_hash, verify_password


def main():
    parser = argparse.ArgumentParser(description="Generate or verify password hashes.")
    subparsers = parser.add_subparsers(title="command", dest="command")
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a hash for the provided password. usage: passuth generate <password>",
        description="Generate a hash for the provided password.",
    )
    generate_parser.add_argument(
        "password",
        type=str,
        help="The password to hash",
    )
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a password against a hash. usage: passuth verify <password> <hash>",
        description="Verify a password against a hash.",
    )
    verify_parser.add_argument(
        "password",
        type=str,
        help="The password to verify",
    )
    verify_parser.add_argument(
        "hash",
        type=str,
        help="The hash to verify the password against.",
    )

    args = parser.parse_args()
    if args.command == "generate":
        print(generate_hash(args.password))  # noqa: T201
    elif args.command == "verify":
        print("true" if verify_password(args.password, args.hash) else "false")  # noqa: T201
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
