from rich import print


def prepare():
    print("I am preparing some data")


def read_data():
    print("I am reading some data")
    return None


def build_lci() -> None:
    print("I am building LCI")
    return None


def lcia_step() -> float:
    print("I am building LCIA")
    return None


def main():
    prepare()
    build_lci()
    lcia_step()
    print("Main is done")


if __name__ == "__main__":
    main()
