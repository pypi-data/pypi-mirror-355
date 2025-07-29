def head[T](xs: T) -> T:
    return xs[0]


def tail[T](xs: T) -> T:
    return xs[1:]


def entrypoint() -> None:
    raise Exception("The entrypoint function is reserved as a placeholder for the compiler. Do not call it directly. Use the @entrypoint decorator to mark a function as the entry point.")