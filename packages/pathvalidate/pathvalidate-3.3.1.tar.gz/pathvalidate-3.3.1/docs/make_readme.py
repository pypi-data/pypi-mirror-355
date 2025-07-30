#!/usr/bin/env python3

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import sys

from path import Path
from readmemaker import ReadmeMaker


PROJECT_NAME = "pathvalidate"
OUTPUT_DIR = ".."


def write_examples(maker: ReadmeMaker) -> None:
    maker.set_indent_level(0)
    maker.write_chapter("Examples")

    example_root = Path("pages").joinpath("examples")
    maker.inc_indent_level()

    maker.write_chapter("Sanitize a filename")
    maker.write_file(example_root.joinpath("sanitize_filename_code.txt"))

    maker.write_chapter("Sanitize a filepath")
    maker.write_file(example_root.joinpath("sanitize_filepath_code.txt"))

    maker.write_chapter("Validate a filename")
    maker.write_file(example_root.joinpath("validate_filename_code.txt"))

    maker.write_chapter("Check a filename")
    maker.write_file(example_root.joinpath("is_valid_filename_code.txt"))

    maker.write_chapter("filename/filepath validator for ``argparse``")
    maker.write_file(example_root.joinpath("argparse_validator.txt"))

    maker.write_chapter("filename/filepath sanitizer for ``argparse``")
    maker.write_file(example_root.joinpath("argparse_sanitizer.txt"))

    maker.write_chapter("filename/filepath validator for ``click``")
    maker.write_file(example_root.joinpath("click_validator.txt"))

    maker.write_chapter("filename/filepath sanitizer for ``click``")
    maker.write_file(example_root.joinpath("click_sanitizer.txt"))

    maker.write_chapter("For more information")
    maker.write_lines(
        [
            "More examples can be found at ",
            f"https://{PROJECT_NAME}.rtfd.io/en/latest/pages/examples/index.html",
        ]
    )


def main() -> int:
    maker = ReadmeMaker(
        PROJECT_NAME,
        OUTPUT_DIR,
        is_make_toc=True,
        project_url=f"https://github.com/thombashi/{PROJECT_NAME}",
    )

    maker.write_chapter("Summary")
    maker.write_introduction_file("summary.txt")
    maker.write_introduction_file("badges.txt")

    maker.write_introduction_file("feature.txt")
    maker.write_introduction_file("cli.txt")

    write_examples(maker)

    maker.write_introduction_file("installation.rst")

    maker.set_indent_level(0)
    maker.write_chapter("Documentation")
    maker.write_lines([f"https://{PROJECT_NAME}.rtfd.io/"])

    maker.write_file(maker.doc_page_root_dir_path.joinpath("sponsors.rst"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
