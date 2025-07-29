# import logging
from parser import NLEParser

if __name__ == "__main__":
    # logging.basicConfig(
    #   level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s"
    # )

    config = {
        "language": "en-us",
    }
    vocabulary = {
        "pronouns": {"he", "she", "it", "this", "that"},
        "verbs": {"take", "look", "use"},
        "objects": {"key", "door", "box"},
    }
    stop_words = {"the", "a", "an", "of", "in", "on", "at", "to"}

    parser = NLEParser(config, vocabulary, stop_words)

    parsed_prompt1 = parser.parse("he take the key")
    parsed_prompt2 = parser.parse("take the key")
    parsed_prompt3 = parser.parse("he look box")

    print("Parsed Prompt 1:", parsed_prompt1)
    print("Parsed Prompt 2:", parsed_prompt2)
    print("Parsed Prompt 3:", parsed_prompt3)
