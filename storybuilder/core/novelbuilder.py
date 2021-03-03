"""Build novel moduler for storybuilder project."""


# Official Libraries


# My Modules
from storybuilder.core.actiondatacreator import get_action_data
from storybuilder.core.contentscreator import get_contents_list
from storybuilder.core.storycodecreator import get_story_code_data
from storybuilder.dataconverter import conv_text_in_action_data_by_tags, conv_text_list_by_tags
from storybuilder.datatypes import ActionData, ActionRecord
from storybuilder.datatypes import OutputData
from storybuilder.datatypes import StoryCode, StoryCodeData
from storybuilder.datatypes import StoryData, StoryRecord
from storybuilder.formatter import format_contents_table_data, format_novel_data, get_breakline
from storybuilder.instructions import apply_instruction_to_action_data
from storybuilder.nametagmanager import NameTagDB
from storybuilder.util import assertion
from storybuilder.util.log import logger


__all__ = (
        'on_build_novel',
        'get_story_code_data_from_story_data_as_novel',
        )


# Main Function
def on_build_novel(story_data: StoryData, tags: dict) -> OutputData:
    assert isinstance(story_data, StoryData)
    assert isinstance(tags, dict)

    contents = get_contents_list(story_data)

    story_code_data = assertion.is_instance(
            get_story_code_data_from_story_data_as_novel(story_data, tags),
            StoryCodeData)

    novels = format_contents_table_data(contents) \
            + ["\n", get_breakline()] \
            + format_novel_data(story_code_data)

    output_data = conv_text_list_by_tags(novels, tags)

    return OutputData(output_data)


# Functions
def get_story_code_data_from_story_data_as_novel(story_data: StoryData, tags: dict) -> StoryCodeData:
    assert isinstance(story_data, StoryData)
    assert isinstance(tags, dict)

    action_data = assertion.is_instance(get_action_data(story_data), ActionData)

    action_data_applied = assertion.is_instance(
            apply_instruction_to_action_data(action_data), ActionData)

    callings = NameTagDB.get_calling_tags()
    action_data_tagfixed = assertion.is_instance(
            conv_text_in_action_data_by_tags(action_data_applied, callings),
            ActionData)

    story_code_data = assertion.is_instance(get_story_code_data(action_data_tagfixed, False),
        StoryCodeData)

    return story_code_data

