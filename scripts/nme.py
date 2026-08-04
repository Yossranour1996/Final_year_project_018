from pathlib import Path
import re


# ضعي هنا مسار المجلد الذي يحتوي كراسات الـTest
FOLDER = Path(r"C:\Users\hp\Desktop\test_sheets")

# الامتدادات المطلوب تعديلها
ALLOWED_EXTENSIONS = {".pdf"}

START_NUMBER = 51
END_NUMBER = 70

# اتركيها True أولًا لمراجعة الأسماء فقط
DRY_RUN = False


def natural_sort_key(path: Path):
    """
    ترتيب طبيعي:
    file2 قبل file10
    """
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", path.name)
    ]


def main():
    if not FOLDER.exists():
        raise FileNotFoundError(
            f"Folder not found: {FOLDER}"
        )

    files = sorted(
        [
            path
            for path in FOLDER.iterdir()
            if path.is_file()
            and path.suffix.lower() in ALLOWED_EXTENSIONS
            and "__sheet_" not in path.stem
        ],
        key=natural_sort_key,
    )

    required_count = END_NUMBER - START_NUMBER + 1

    if len(files) != required_count:
        raise ValueError(
            f"Expected exactly {required_count} files, "
            f"but found {len(files)} files.\n"
            f"Folder: {FOLDER}"
        )

    rename_operations = []

    for sheet_number, old_path in zip(
        range(START_NUMBER, END_NUMBER + 1),
        files,
    ):
        suffix_to_add = f"__sheet_{sheet_number:03d}"

        new_name = (
            old_path.stem
            + suffix_to_add
            + old_path.suffix
        )

        new_path = old_path.with_name(new_name)

        if new_path.exists():
            raise FileExistsError(
                f"Target file already exists: {new_path}"
            )

        rename_operations.append(
            (old_path, new_path)
        )

        print(f"{old_path.name}")
        print(f"-> {new_path.name}")
        print("-" * 80)

    if DRY_RUN:
        print("\nDRY RUN: no files were renamed.")
        print(
            "After checking the order, change "
            "DRY_RUN = False and run again."
        )
        return

    for old_path, new_path in rename_operations:
        old_path.rename(new_path)

    print(
        f"\nDone. Renamed {len(rename_operations)} files."
    )


if __name__ == "__main__":
    main()