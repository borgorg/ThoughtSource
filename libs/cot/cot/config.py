import json
import pkgutil
from dataclasses import dataclass, field
from typing import List

FRAGMENTS = json.loads(pkgutil.get_data(__name__, "fragments.json"))


@dataclass
class Config:
    """Class for keeping track of the config variables:
    "idx_range": tuple(int,int) - Determines which indices the generate_and_extract routine is applied to,
        if idx not within idx_range do nothing and return item. Default: "all" (All items are used)
    "multiple_choice_answer_format": str - How the list of multiple choice answer is formatted and indexed
        "Letters" (A,B,C,...), "Numbers" (1,2,3,...), "None" (no index), Default: "Letters" (A,B,C,...)
        # TODO: change name to multiple_choice_formatting, add None option
    "instruction_keys": list(str) - Determines which instruction_keys are used from fragments.json,
        the corresponding string will be inserted under "instruction" in the fragments. Default: "all" (All used)
    "cot_trigger_keys": list(str) - Determines which cot triggers are used from fragments.json,
        the corresponding string will be inserted under "cot_trigger" in the fragments. Default: None (All are used)
    "answer_extraction_keys": list(str) - Determines which answer extraction prompts are used from fragments.json,
        the corresponding string will be inserted under "answer" in the fragments. Default: None (All are used)
    "template_cot_generation": string - is the model input in the text generation step, variables in brackets.
        Only variables of this list are allowed: "instruction", 'question", "answer_choices", "cot_trigger"
        Default:
            '''{instruction}

            {question}
            {answer_choices}

            {cot_trigger}'''
    "template_answer_extraction": string - is the model input in the answer extraction step, variables in brackets.
        Only variables of this list are allowed: "instruction", 'question", "answer_choices", "cot_trigger",
        "cot", "answer"
        Default:
            '''{instruction}

            {question}
            {answer_choices}

            {cot_trigger}{cot}
            {answer_extraction}'''
    "author" : str - Name of the person responsible for generation, Default: ""
    "api_service" str - Name of the used api service: "openai" or "huggingface_hub",
        or a mock api service "mock_api" for debugging, Default: "huggingface_hub"
    "engine": str -  Name of the engine used, look at website of api which models are
        available, e.g. for "openai": "text-davinci-002", Default: "google/flan-t5-xl"
    "temperature": float - Describes how much randomness is in the generated output,
        0.0 means the model will only output the most likely answer, 1.0 means
        the model will also output very unlikely answers, defaults to 0
    "max_tokens": int - Maximum length of output generated by model , Default: 128
    "api_time_interval": float - Pause between two api calls in seconds, Default: 1.0
    "warn": bool - Print warnings preventing excessive api usage, Default: True
    name: str
    unit_price: float
    quantity_on_hand: int = 0
    """

    idx_range: tuple or "all" = "all"
    multiple_choice_answer_format: str = "Letters"
    instruction_keys: list or "all" = None
    # Passing a default list as an argument to dataclasses needs to be done with a lambda function
    # https://stackoverflow.com/questions/52063759/passing-default-list-argument-to-dataclasses
    cot_trigger_keys: List = field(default_factory=lambda: ["kojima-01"])
    answer_extraction_keys: List = field(default_factory=lambda: ["kojima-01"])
    template_cot_generation: str = (
        "{instruction}\n\n{question}\n{answer_choices}\n\n{cot_trigger}"
    )
    template_answer_extraction: str = "{instruction}\n\n{question}\n{answer_choices}\n\n{cot_trigger}{cot}\n{answer_extraction}"
    author: str = ""
    api_service: str = "huggingface_hub"
    engine: str = "google/flan-t5-xl"
    temperature: int or float = 0.0
    max_tokens: int = 128
    api_time_interval: int or float = 1.0
    verbose: bool = True
    warn: bool = True
    # TODO: add a way to set the api key?
    # TODO: add an option to add None as a key. At the moment this is done automatically.

    def __post_init__(self):
        # replace all keys (or non given keys) in config with the corresponding values

        # Inserts None at index 0 of instruction_keys to query without an explicit instruction
        # TODO rethink this, maybe add option to disable this
        if self.instruction_keys == "all":
            self.instruction_keys = [None] + list(FRAGMENTS["instructions"].keys())
        elif not self.instruction_keys:
            self.instruction_keys = [None]

        if self.cot_trigger_keys == "all":
            self.cot_trigger_keys = [None] + list(FRAGMENTS["cot_triggers"].keys())
        elif not self.cot_trigger_keys:
            self.cot_trigger_keys = [None]

        if self.answer_extraction_keys == "all":
            self.answer_extraction_keys = [None] + list(
                FRAGMENTS["answer_extractions"].keys()
            )
        elif not self.answer_extraction_keys:
            self.answer_extraction_keys = [None]

        # check if the templates contain only allowed keys
        import re

        input_variables = re.findall(
            "{(.*?)}", self.template_cot_generation + self.template_answer_extraction
        )
        allowed_variables = [
            "instruction",
            "question",
            "answer_choices",
            "cot_trigger",
            "cot",
            "answer_extraction",
        ]
        for variable in input_variables:
            if variable not in allowed_variables:
                raise ValueError(
                    f"Given variable '{variable}' is not allowed in templates. Allowed variables are: {allowed_variables}"
                )

        # check if template matches the given config
        # TODO: adapt to new template structure, no more template dict.
        # assert (self.instruction_keys == [None]) == ("instruction" not in input_variables), (
        #     '''There seems to be a mismatch between the template and the provided keys in the config.
        #         If {template_var} is in the template, {config_var} has to be specified and cannot be [None].
        #         if {template_var} is not in the template, {config_var} has to be [None] or not specified.
        #         '''
        #     )

        # if self.instruction_keys != ["None"]:

        # for (config_var, template_var) in zip(
        #     [self.instruction_keys, self.cot_trigger_keys, self.answer_extraction_keys],
        #     ["instruction", "cot_trigger", "answer_extraction"]
        # ):
        #     assert (config_var != ["None"]) == (template_var in input_variables), (

        # simple checks
        if self.idx_range != "all":
            assert isinstance(self.idx_range, tuple), "idx_range must be a tuple"
            assert isinstance(
                self.idx_range[0], int
            ), "idx_range must be a tuple of ints"
            assert isinstance(
                self.idx_range[1], int
            ), "idx_range must be a tuple of ints"
            assert (
                self.idx_range[0] < self.idx_range[1]
            ), "idx_range must be a tuple of ints with idx_range[0] < idx_range[1]"

        if self.multiple_choice_answer_format != "Letters":
            assert isinstance(
                self.multiple_choice_answer_format, (str, type(None))
            ), "multiple_choice_answer_format must be str or None"
            assert self.multiple_choice_answer_format in [
                "Letters",
                "Numbers",
                None,
            ], "multiple_choice_answer_format must be 'Letters', 'Numbers' or None"

        if self.instruction_keys != "all":
            assert isinstance(
                self.instruction_keys, list
            ), "instruction_keys must be a list"
            assert all(
                isinstance(key, (str, type(None))) for key in self.instruction_keys
            ), "instruction_keys must be a list of strings"

        if self.cot_trigger_keys != "all":
            assert isinstance(
                self.cot_trigger_keys, list
            ), "cot_trigger_keys must be a list"
            assert all(
                isinstance(key, (str, type(None))) for key in self.cot_trigger_keys
            ), "cot_trigger_keys must be a list of strings"

        if self.answer_extraction_keys != "all":
            assert isinstance(
                self.answer_extraction_keys, list
            ), "answer_extraction_keys must be a list"
            assert all(
                isinstance(key, (str, type(None)))
                for key in self.answer_extraction_keys
            ), "answer_extraction_keys must be a list of strings"

        assert isinstance(
            self.template_cot_generation, str
        ), "template_cot_generation must be a string"
        assert isinstance(
            self.template_answer_extraction, str
        ), "template_answer_extraction must be a string"

        assert isinstance(self.author, str), "author must be a string"
        assert isinstance(self.api_service, str), "api_service must be a string"
        assert isinstance(self.engine, str), "engine must be a string"
        assert isinstance(self.temperature, (int, float)), "temperature must be a float"
        assert isinstance(self.max_tokens, int), "max_tokens must be an int"
        assert isinstance(
            self.api_time_interval, (int, float)
        ), "api_time_interval must be a int or float"
        assert isinstance(self.verbose, bool), "verbose must be a bool"
        assert isinstance(self.warn, bool), "warn must be a bool"

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
