import os

if __name__ == "__main__":
    ver_path = os.path.join(os.path.dirname(__file__), "VERSION")
    with open(ver_path, "r") as f:
        print(f.read())
