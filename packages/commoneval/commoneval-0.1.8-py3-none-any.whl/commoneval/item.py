"""Define the Item class.

An Item is a single pairing of response and prompt for LLM evaluation, along with other metadata.

See tests/src/test_item.py for examples of how to use this class.

"""

from dataclasses import dataclass, field
import json
import re
import sys
from typing import Any, IO, Type

try:
    from enum import StrEnum  # Available in Python 3.11+
except ImportError:
    # Fallback for Python < 3.11
    from enum import Enum

    class StrEnum(str, Enum):
        pass


# deal with version differencs for StrEnum value checking
def is_valid_enum_value(value: str, enum_class: Type[StrEnum]) -> bool:
    """Check if a value is a valid member of an enum class."""
    if sys.version_info >= (3, 12):
        # Python 3.12+ allows direct containment
        return value in enum_class
    else:
        # Python 3.11 and earlier require manual check
        return value in enum_class._value2member_map_


# enumerate values for moddality
class Modality(StrEnum):
    """Enumerates the types of responses that the prompt expects."""

    # closed-set responses
    #
    BOOLEAN = "boolean"
    CHOICEOF2 = "choiceof2"
    CHOICEOF3 = "choiceof3"
    CHOICEOF4 = "choiceof4"
    CHOICEOF5 = "choiceof5"
    TERNARY = "ternary"
    # open-ended responses
    CLOZE = "cloze"
    SINGLEVALUE = "singlevalue"
    SHORTPROSE = "shortprose"
    LONGPROSE = "longprose"


class Ternary(StrEnum):
    """Enumerate strings representing boolean values plus 'Unknown'."""

    TRUE = "True"
    FALSE = "False"
    UNKNOWN = "Unknown"


@dataclass
class Item:
    """An Item is a single pairing of response and prompt for LLM evaluation, along with other metadata."""

    # The ID of the item
    identifier: str
    # identifies the type of response that the prompt expects
    modality: Modality
    # The prompt used to generate the response
    prompt: str
    # The expected 'gold standard' response: LLM output is compared to this
    response: bool | str
    # optional values below here
    # Content that justifies the reference answer
    support: str = ""
    # Directions for how the LLM should respond to the prompt
    taskPrompt: str = ""
    # The difficulty of the item, from 0.0 to 1.0
    difficulty: float = 0.0
    # stash other data here if needed
    _otherargs: dict[str, Any] = field(default_factory=dict)
    _choiceof2values: set[str] = field(default_factory=lambda: {"A", "B"})
    _choiceof3values: set[str] = field(default_factory=lambda: {"A", "B", "C"})
    _choiceof4values: set[str] = field(default_factory=lambda: {"A", "B", "C", "D"})
    _choiceof5values: set[str] = field(
        default_factory=lambda: {"A", "B", "C", "D", "E"}
    )

    def __post_init__(self):
        """Post-initialization checks for the Item class."""
        assert re.fullmatch(
            r"[-a-zA-Z0-9_.]+", self.identifier
        ), f"Identifier {self.identifier} has invalid characters."
        if self.modality != Modality.BOOLEAN:
            assert len(self.response) > 0, "Response is empty."
        match self.modality:
            # closed-set responses
            case Modality.BOOLEAN:
                assert self.response in {
                    True,
                    False,
                }, "Response is not a valid boolean."

            case Modality.CHOICEOF2:
                assert (
                    self.response in self._choiceof2values
                ), "Response is not a valid choice of 2."
            case Modality.CHOICEOF3:
                assert (
                    self.response in self._choiceof3values
                ), "Response is not a valid choice of 3."
            case Modality.CHOICEOF4:
                assert (
                    self.response in self._choiceof4
                ), "Response is not a valid choice of 4."
            case Modality.CHOICEOF5:
                assert (
                    self.response in self._choiceof5
                ), "Response is not a valid choice of 5."
            case Modality.TERNARY:
                assert is_valid_enum_value(
                    self.response, Ternary
                ), "Response is not a valid ternary value."
            # open-ended responses
            case Modality.CLOZE:
                assert "___" in self.prompt, "Prompt is missing ___ cloze indicator."
            # nothing to check for other modalities
        assert 1.0 >= self.difficulty >= 0.0, "Difficulty must be between 0.0 and 1.0."

    def __repr__(self) -> str:
        """Return a string representation of the Item."""
        if self.modality != Modality.BOOLEAN:
            if len(self.prompt) > 20:
                promptstr = self.prompt[:17] + "..."
            else:
                promptstr = self.prompt
            if len(self.response) > 20:
                responsestr = self.response[:17] + "..."
            else:
                responsestr = self.response
        else:
            promptstr = self.prompt
        responsestr = self.response
        return f"<Item({self.identifier!r}, {self.modality}): {promptstr!r}->{responsestr!r}>"

    def asdict(self) -> dict[str, Any]:
        """Return the Item as a dictionary for serialization."""
        outdict = {
            "identifier": self.identifier,
            "modality": self.modality.value,
            "prompt": self.prompt,
            "response": self.response,
        }
        if self.support:
            outdict["support"] = self.support
        if self.taskPrompt:
            outdict["taskPrompt"] = self.taskPrompt
        return outdict

    def write_jsonline(self, fp: IO[str]) -> str:
        """Return the Item as a JSONL string."""
        json.dump(self.asdict(), fp)
        fp.write("\n")


# Need a subclass for multiple responses: assume for base Item that there's a single response
# need to think through lists or dicts for responses


# Subclass of Item for templated items
# THIS NEEDS WORK: parking code here for now
@dataclass
class TemplatedItem(Item):
    """A subclass of Item for templated items."""

    # if the prompt is templated, the values for instantiating the template
    promptVariables: dict[str, str] = field(default_factory=dict)
    # if the prompt is templated, the values for the responses
    responseVariables: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Post-initialization checks for the TemplatedItem class."""
        super().__post_init__()
        # check that the prompt variables are valid
        for key in self.promptVariables:
            assert key in self.get_template_keys(), f"Invalid prompt variable {key}."
        # check that the response variables are valid
        for key in self.responseVariables:
            assert key in self.get_template_keys(), f"Invalid response variable {key}."
        if "{" in self.prompt:
            assert self.isTemplated, "Prompt is templated but isTemplated is False"
            assert len(self.get_template_keys()) == len(
                self.response
            ), "Prompt is templated but number of keys does not match number of responses"
            assert bool(
                self.promptVariables
            ), "Prompt is templated but no prompt variables provided"
            assert bool(
                self.responseVariables
            ), "Prompt is templated but no response variables provided"

    def get_template_keys(self) -> set[str]:
        """If the prompt is templated, return the keys in the template.

        This identifies brackets in the string, ensures they are
        correctly paired and not empty, and returns the set of
        keys. Any duplicate keys will be treated the same.

        If the prompt is not templated, return an empty set.

        """
        if not self.isTemplated:
            return set()
        else:
            keys = set()
            stack = []
            for i, c in enumerate(self.prompt):
                if c == "{":
                    stack.append(i)
                elif c == "}":
                    if not stack:
                        raise ValueError(f"Unmatched '}}' at index {i} in prompt.")
                    start = stack.pop()
                    key = self.prompt[start + 1 : i]
                    if not key:
                        raise ValueError(
                            f"Empty key in prompt at indices {start} to {i}."
                        )
                    keys.add(key)
            if stack:
                raise ValueError(f"Unmatched '{{' at indices {stack} in prompt.")
            return keys

    def generate_prompts(self) -> list[str]:
        """Generate the prompts from the template and the variables."""
        return [
            self.prompt.replace("{" + key + "}", value)
            for index, key in list(enumerate(self.get_template_keys()))
            for value in self.promptVariables[key]
        ]
