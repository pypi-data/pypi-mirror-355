from pprint import pprint
from . import generate_option


def main() -> None:
    """Run a simple demonstration."""
    line_data = {
        "labels": ["Mon", "Tue", "Wed"],
        "values": [820, 932, 901],
        "name": "demo",
    }

    pie_data = {
        "labels": ["Search Engine", "Direct"],
        "values": [1048, 735],
        "name": "traffic",
    }

    pprint(generate_option("line", line_data))
    pprint(generate_option("pie", pie_data))


if __name__ == "__main__":
    main()
