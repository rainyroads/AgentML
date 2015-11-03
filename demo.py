#!/bin/env python3
import logging
from agentml import AgentML


def demo():
    aml = AgentML(logging.ERROR)
    aml.load_directory('demo/lang')
    aml.interpreter()


if __name__ == '__main__':
    demo()
