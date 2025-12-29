#!/usr/bin/env python3
"""
Workplace Training Platform Test Agent

A computer use agent that autonomously navigates and tests
a workplace training platform by watching videos, answering
assessments, and verifying user flow completion.
"""

from training_agent import TrainingAgent


def main():
    agent = TrainingAgent()
    agent.run()


if __name__ == "__main__":
    main()
