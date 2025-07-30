from sys import argv
from time import sleep
from justserver.logging import logger


def app():
    print(argv)
    while True:
        sleep(1)
        print(argv)


