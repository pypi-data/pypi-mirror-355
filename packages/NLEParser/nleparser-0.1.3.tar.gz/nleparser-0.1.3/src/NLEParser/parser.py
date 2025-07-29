import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NLEParser:
    def __init__(self, config: dict, vocabulary: dict, stop_words: set):
        """
        The parser it's initialized with the static knowledge of the language.
        """
        self.config = config
        self.vocabulary = vocabulary
        self.stop_words = stop_words
        self.last_referenced_object: Optional[dict] = None

    def _process_pronouns(self, tokens: list[str]) -> list[str]:
        """
        Substitutes pronouns for the last object referenced
        """
        pronouns = self.vocabulary["pronouns"]
        if not self.last_referenced_object:
            logger.debug("No last referenced object. Tokens unchanged: %s", tokens)
            return tokens  # No tokens to substitute

        new_tokens = []
        for token in tokens:
            if token in pronouns:
                logger.debug(
                    "Substituting pronoun '%s' with '%s'",
                    token,
                    self.last_referenced_object["canonical_name"],
                )
                new_tokens.append(self.last_referenced_object["canonical_name"])
            else:
                new_tokens.append(token)
        logger.debug("Tokens after pronoun processing: %s", new_tokens)
        return new_tokens

    def parse(self, command_input: str) -> Optional[dict]:
        """
        Receives a string from the player and returns a structured command.
        """
        logger.info("Parsing input: %s", command_input)
        # Lexical Analysis
        tokens = command_input.lower().split()
        logger.debug("Tokens after split: %s", tokens)
        cleaned_tokens = [t for t in tokens if t not in self.stop_words]
        logger.debug("Tokens after stop word removal: %s", cleaned_tokens)

        # Context resolution
        resolved_tokens = self._process_pronouns(cleaned_tokens)
        if not resolved_tokens:
            logger.warning("No tokens after pronoun processing.")
            return None

        logger.info("Resolved tokens: %s", resolved_tokens)

        # Debug block code
        verbs = self.vocabulary["verbs"]
        for token in resolved_tokens:
            if token in verbs:
                logger.info("Verb found: %s", token)

        objects = self.vocabulary["objects"]
        for token in resolved_tokens:
            if token in objects:
                logger.info("Object found: %s", token)

        # Syntax Analysis
        parsed_command = self._syntactic_analysis(resolved_tokens)
        return parsed_command

    def _syntactic_analysis(self, tokens: list[str]) -> Optional[dict]:
        """
        Analyse the structure of the tokens and return a strucutred command.
        Output example: {"verb": "pick", "object": "key"}
        """
        verbs = self.vocabulary["verbs"]
        objects = self.vocabulary["objects"]
        result = {}

        for i, token in enumerate(tokens):
            if token in verbs:
                result["verb"] = token
                logger.debug("Verb found, syntactic Analysis: %s", token)
                # Procura o próximo token como objeto
                if i + 1 < len(tokens) and tokens[i + 1] in objects:
                    logger.debug("Object found after verb: %s", tokens[i + 1])
                    result["object"] = tokens[i + 1]
                break

        if "verb" in result:
            return result
        return None

    def update_context(self, object: dict):
        """
        Called in the main loop to update the last object of a well-succeeded command
        """
        logger.info("[Parser] Context updated. Last object: %s", object)
        self.last_referenced_object = object
