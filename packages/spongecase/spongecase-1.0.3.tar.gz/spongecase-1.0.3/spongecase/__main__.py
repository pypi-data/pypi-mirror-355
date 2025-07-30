import random
import sys


# High `p_flip` favors alternating case (1.0 forces all alternating); low
# `p_flip` favors same case (0.0 forces all same)
def spongify(string, p_flip=0.95):
    return "".join(spongify_generator(string, p_flip=p_flip))


def spongify_generator(string, p_flip):
    upper = random.choice([True, False])

    for char in string.lower():
        if char.isalpha():
            upper = random.random() >= abs(1 - p_flip - upper)
            yield char.upper() if upper else char
        else:
            yield char


def main():
    try:
        for line in sys.stdin:
            print(spongify(line.rstrip()))

        return 0
    except KeyboardInterrupt:
        # ^C: exit quietly (but still 1, not 0) instead of printing stack trace
        return 1


if __name__ == "__main__":
    sys.exit(main())
