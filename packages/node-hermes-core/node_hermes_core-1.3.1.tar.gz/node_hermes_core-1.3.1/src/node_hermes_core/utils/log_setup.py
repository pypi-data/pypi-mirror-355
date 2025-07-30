import coloredlogs # type: ignore


def setup_logging():
    coloredlogs.install(
        fmt="(%(relativeCreated)6d) [%(levelname)s] %(name)s: %(message)s",
        level="INFO",
        # level_styles=dict(
        #     debug={"color": "yellow"},
        #     info={"color": "white"},
        #     warning={"color": "red"},
        #     error={"color": "red"},
        # ),
        field_styles=dict(
            relativeCreated={"color": "black"},
            levelname={"color": "white", "bold": True},
            name={"color": "blue"},
        ),
    )
