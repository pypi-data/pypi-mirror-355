# %%
import site
import subprocess
import json
import argparse
from pathlib import Path
from typing import List


# %%
def get_package_size(package_path: Path) -> float:
    """
    Get the size of a package (directory or file) in MB.


    Parameters:
    -----------
    package_path: Path, required
        Path to the package

    Returns:
    -----------
    total_size: float
        A float of package size in megabytes
    """

    if package_path.is_dir():
        # If it's a directory, sum the size of all files in the directory
        total_size = sum(
            f.stat().st_size for f in package_path.rglob("*") if f.is_file()
        )
    else:
        # If it's a single file (like a .dist-info), just get its size
        total_size = package_path.stat().st_size
    return total_size / (1024**2)  # Convert to MB


def list_installed_packages_sizes(package_names=None):
    """
    List all installed packages in site-packages and their sizes.

    """
    site_packages_paths = (
        site.getsitepackages()
    )  # Get list of site-packages directories

    package_sizes = {}
    for site_package in site_packages_paths:
        site_package_path = Path(site_package)
        if site_package_path.exists():
            for package in site_package_path.iterdir():
                if package.is_dir() or package.suffix in {".py.egg-info", ".dist-info"}:
                    size = get_package_size(package)
                    package_sizes[package.name] = size

    if package_names is not None:
        package_names = {name.lower() for name in package_names}
        package_sizes = {
            k: v for k, v in package_sizes.items() if k.lower() in package_names
        }

    large_packages = {}
    small_packages_total_size = 0
    small_packages_count = 0
    total_size = 0

    for package_name, size in package_sizes.items():
        total_size += size
        if size >= 1:
            large_packages[package_name] = size
        else:
            small_packages_count += 1
            small_packages_total_size += size

    sorted_large_packages = sorted(
        large_packages.items(), key=lambda x: x[1], reverse=True
    )

    print(f"Total size of all packages: {total_size:.2f} MB")
    print("=" * 50)
    print("Packages larger than  1MB: ")
    for package_name, size in sorted_large_packages:
        print(f"{package_name}: {size:.2f} MB")
    print(f"\nPackages smaller than 1 MB: {small_packages_count} packages")
    print(
        f"Combined size of packages smaller than 1 MB: {small_packages_total_size:.2f} MB"
    )


def get_pip_packages():
    """
    Gets a list of packages in json using "pip list --format=json"

    If main_only is True, limits to the main group (excluding dev).
    """
    res = subprocess.run(
        ["uv", "pip", "list", "--format=json"], capture_output=True, text=True
    )

    try:
        packages = json.loads(res.stdout)
    except json.JSONDecodeError:
        print("Error: Failed to parse uv pip list output")
        return []

    return packages


def write_deps_json(data: dict, file_path: Path):
    """
    Get list of packages, check each package size, and append to the dict before writing to json

    Parameters:
    -----------
    data: dict, Required
        the dictionary of packages from the get_pip_packages method
    file_path: Path, Required
        the posix path to write the JSON file to

    Returns:
    --------
    f, the JSON file including the path it is stored on.
    """
    site_packages_paths = site.getsitepackages()
    enriched_data = []

    for package in data:
        package_name = package["name"]
        package_version = package["version"]
        package_size = None

        # Attempt to find the package in site-packages
        for site_package in site_packages_paths:
            site_package_path = Path(site_package)

            # Look for folders or files that match the package name
            potential_matches = list(site_package_path.glob(f"{package_name}*"))

            if potential_matches:
                # Use the first match found
                package_path = potential_matches[0]
                package_size = get_package_size(package_path)
                break

        # Append to enriched data
        enriched_data.append(
            {
                "name": package_name,
                "version": package_version,
                "size_MB": round(package_size, 2) if package_size is not None else None,
            }
        )

    # Write to JSON
    file_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    with open(file_path, "w") as f:
        json.dump(enriched_data, f, indent=2)

    return file_path


def read_requirements_file(path: Path) -> List[str]:
    """
    Read a pip-compile style requirements file and return package names only.
    """
    packages = set()

    with open(path) as f:
        for line in f:
            line = line.strip()

            if line.startswith("#") or not line or line.startswith("    "):
                continue
            # Remove extras, version pins, hashes, etc.
            name = line.split("==")[0].split(">=")[0].split("<=")[0].strip()
            packages.add(name)
    return list(packages)


def get_installed_package_versions(package_names=None):
    """ """
    res = subprocess.run(
        ["uv", "pip", "list", "--format=json"], capture_output=True, text=True
    )
    installed = json.loads(res.stdout)
    if package_names is None:
        return installed
    filtered = [
        pkg
        for pkg in installed
        if pkg["name"].lower() in {n.lower() for n in package_names}
    ]
    return filtered


# %%
def main():
    description = """depsize: Get the total size of installed python dependencies in megabytes (MB).
    Run 'depsize total' to get total size of dependencies, including the largest
    Run 'depsize --o FILE' to export dependencies as JSON, 
        f.ex 'depsize --o data/packages.json'
    Add '--from' to 'depsize total' and 'depsize --o' to measure size of main and dev dependencies, 
        f.ex 'depsize total --from requirements-main.txt'"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "command",
        nargs="?",
        choices=["total"],
        help="Optional: Use 'total' to print size summary in terminal.",
    )
    parser.add_argument(
        "--o",
        "--output",
        dest="output_path",
        type=Path,
        help="Path to output JSON file, f.ex data/packages.json",
    )
    parser.add_argument(
        "--from",
        dest="requirements_path",
        type=Path,
        help="Path to requirements.txt file",
    )

    args = parser.parse_args()

    # handle optional --from argument
    package_names = None
    if args.requirements_path:
        package_names = read_requirements_file(args.requirements_path)
        if not package_names:
            print(
                f"No packages found in {args.requirements_path}. Is the file empty or does it only contain comments?"
            )

    # command: depsize total [--from]
    if args.command == "total":
        list_installed_packages_sizes(package_names)

    # command: depsize --o FILE [--from]
    elif args.output_path:
        data = get_installed_package_versions(package_names)
        output_path = write_deps_json(data, args.output_path)
        print(f"Dependencies written to {output_path}")

    # fallback usage message
    else:
        print(description)


if __name__ == "__main__":
    main()
# %%
