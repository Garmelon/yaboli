from setuptools import setup

setup(
        name="yaboli",
        version="0.1.0",
        packages=["yaboli"],
        install_requires=["websockets==7.0"],
)

# When updating the version, also:
# - set a tag to the update commit
# - update the changelog
