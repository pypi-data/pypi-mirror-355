import argparse
from pprint import pprint

from chaos_box.logging import setup_logger

logger = setup_logger(__name__)


def gen_next_row(prev_row: list):
    next_row = [1]
    for i in range(1, len(prev_row)):
        next_row.append(prev_row[i - 1] + prev_row[i])

    next_row.append(1)
    return next_row


def gen_pascal_triangle(num_rows: int):
    pascal_triangle = []
    for i in range(num_rows):
        if i == 0:
            pascal_triangle.append([1])
        else:
            pascal_triangle.append(gen_next_row(pascal_triangle[i - 1]))

    return pascal_triangle


def main():
    parser = argparse.ArgumentParser(description="Generate Pascal's Triangle")
    parser.add_argument(
        "num_rows", type=int, help="Number of rows in Pascal's Triangle"
    )
    args = parser.parse_args()

    if args.num_rows < 0:
        logger.warning("Number of rows must be a non-negative integer.")
        return

    pprint(gen_pascal_triangle(args.num_rows))


if __name__ == "__main__":
    main()
