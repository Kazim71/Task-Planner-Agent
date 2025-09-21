import sys
import pkg_resources

def check_python_version():
    required = (3, 12)
    if sys.version_info[:2] != required:
        print(f"ERROR: Python {required[0]}.{required[1]} required, found {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"Python version OK: {sys.version_info.major}.{sys.version_info.minor}")

def check_psycopg2_binary():
    try:
        version = pkg_resources.get_distribution("psycopg2-binary").version
        if version != "2.9.10":
            print(f"ERROR: psycopg2-binary==2.9.10 required, found {version}")
            sys.exit(1)
        print(f"psycopg2-binary version OK: {version}")
    except Exception as e:
        print("ERROR: psycopg2-binary not installed or not found.")
        sys.exit(1)

if __name__ == "__main__":
    check_python_version()
    check_psycopg2_binary()
