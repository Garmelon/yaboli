from setuptools import setup

setup(
        name="yaboli",
        version="1.1.2",
        packages=["yaboli"],
        install_requires=["websockets==7.0"],
)

# When updating the version, also:
# - update the README.md installation instructions
# - update the changelog
# - set a tag to the update commit

# Meanings of version numbers
#
# Format: a.b.c
#
# a - increased when: major change such as a rewrite
# b - increased when: changes breaking backwards compatibility
# c - increased when: minor changes preserving backwards compatibility
#
# To specify version requirements for yaboli, the following format is
# recommended if you need version a.b.c:
#
# yaboli >=a.b.c, <a.b+1.c
#
# "b+1" is the version number of b increased by 1, not "+1" appended to b.
