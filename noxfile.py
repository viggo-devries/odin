import nox
from nox.sessions import Session


@nox.session(python=("3.8", "3.10", "3.11"))
def tests(session: Session):
    # fmt: off
    session.run(
        "poetry", "export",
        "--with=dev",
        "--output=requirements.txt",
        "--extras=toml",
        "--extras=yaml",
        "--extras=arrow",
        "--extras=msgpack",
        external=True,
    )
    # fmt: on
    session.install("-Ur", "requirements.txt")
    session.run("pytest")
