from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from ..reflection.types.base import ConceptType
from .noun_phrase import NounPhrases

T = TypeVar("T")
NounPhrasesStringLiteral = TypeVar("NounPhrasesStringLiteral", bound=str)


class Question(Generic[NounPhrasesStringLiteral, T]):
    """
    Represents a question to be asked to the user.

    Args:
        concept_name: The name of the concept whose value you want to ask for.
        concept_type: The type that you expect the answer to be.
        choices: The choices for the user to select (if any).
        text: The text you want to present to the user (if any).
    """

    noun_phrases: NounPhrases
    concept_type: ConceptType
    choices: List[T]
    text: Optional[str]

    def __init__(self, concept_name: NounPhrasesStringLiteral, concept_type: Type[T], choices: Optional[List[T]] = None, text: Optional[str] = None):
        """
        Initialize a Question object.

        Args:
            concept_name: The name of the concept whose value you want to ask for.
            concept_type: The type that you expect the answer to be.
            choices: The choices for the user to select (if any).
            text: The text you want to present to the user (if any).
        """
        from ..reflection.factory.types import ConceptTypeFactory

        self.noun_phrases = NounPhrases.from_str(concept_name)
        self.concept_type = ConceptTypeFactory.from_type(concept_type)
        self.choices = choices if choices else []
        self.text = text

    def __hash__(self) -> int:
        return hash(self.noun_phrases)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Question) and hash(self) == hash(other)

    def __str__(self) -> str:
        ret = "Question("
        nps_text = str(self.noun_phrases)
        if self.text:
            ret += f"{self.text}, "

        ret += f"noun_phrases='{nps_text}'"

        if self.choices:
            ret += f", choices={self.choices}"

        return ret + ")"

    def __repr__(self) -> str:
        return str(self)


class AnswerStorage(ABC):
    @abstractmethod
    def get(self, concept_noun_phrases: NounPhrases) -> Optional[Any]:
        raise NotImplementedError()

    @abstractmethod
    def set(self, concept_noun_phrases: NounPhrases, answer_value: Any):
        raise NotImplementedError()

    @abstractmethod
    def clear(self):
        raise NotImplementedError()

    @abstractmethod
    def unset(self, concept_noun_phrases: NounPhrases, fail_if_not_set: bool):
        raise NotImplementedError()


class InMemoryAnswerStorage(AnswerStorage):
    def __init__(self):
        self._answer_map: Dict[str, Any] = {}

    def get(self, concept_noun_phrases: NounPhrases) -> Optional[Any]:
        concept_name = str(concept_noun_phrases)
        return self._answer_map.get(concept_name)

    def set(self, concept_noun_phrases: NounPhrases, answer_value: Any):
        concept_name = str(concept_noun_phrases)
        self._answer_map[concept_name] = answer_value

    def unset(self, concept_noun_phrases: NounPhrases, fail_if_not_set: bool):
        concept_name = str(concept_noun_phrases)
        if concept_name in self._answer_map:
            del self._answer_map[concept_name]
        elif fail_if_not_set:
            raise ValueError(f"Key '{concept_name}' is not set")

    def clear(self):
        self._answer_map.clear()


# Use the InMemoryAnswerStorage by default
answer_storage = InMemoryAnswerStorage()


def get_from_context(concept_noun_phrases: NounPhrases) -> Optional[Any]:
    return answer_storage.get(concept_noun_phrases)


def set_answer(concept_noun_phrases: NounPhrases, answer_value: Any):
    answer_storage.set(concept_noun_phrases, answer_value)


def unset_answer(concept_noun_phrases: NounPhrases, fail_if_not_set: bool = False):
    answer_storage.unset(concept_noun_phrases, fail_if_not_set)


def clear_answers():
    answer_storage.clear()


def ask(
    concept_name: NounPhrasesStringLiteral, concept_type: Type[T], text: Optional[str] = None, choices: Optional[List[T]] = None
) -> Union[T, Question[NounPhrasesStringLiteral, T]]:
    """
    Ask a question and get an answer (if available) or a Question object to be
    returned to the user.

    Args:
        concept_name: The unique name of the concept whose value you want to
            ask for.
        concept_type: The type that you expect the answer to be.
        choices: The choices for the user to select (if any).
        text: The text you want to present to the user (if any).

    Returns:
        Answer containing the value from the answer map, typed as T (the
        `concept_type`) or a Question (typed as `Question[Literal[concept_name], T]`)
        if the question is not answered yet.
    """
    possible_answer = get_from_context(NounPhrases.from_str(concept_name))
    if possible_answer is not None:
        if not choices or possible_answer in choices:
            return possible_answer

    return Question(concept_name, concept_type, choices, text)
