import platform
import resource

def extender() -> None:
    """
        Function to extend Resource allocation.

        Args:
            None

        Retruns:
            None
    """
    try:
        os = platform.system()
        if os == "Linux" or os == "Darwin":
            soft , hard = resource.getrlimit(resource.RLIMIT_NOFILE)
            new_limit = 1000000
            resource.setrlimit(resource.RLIMIT_NOFILE,(new_limit,hard))

    except Exception as Ue:
        print(f"Unexpected Error [modules.extender]: {Ue}")

