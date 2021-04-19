"""Build Struct module."""

# Official Libraries


# My Modules
from stobu.core.nametagcreator import get_calling_tags
from stobu.formats.struct import format_structs_data
from stobu.syss import messages as msg
from stobu.tools.translater import translate_tags_text_list
from stobu.types.action import ActionsData, ActionRecord, ActDataType, ActType
from stobu.types.action import NORMAL_ACTIONS
from stobu.types.element import ElmType
from stobu.types.output import OutputsData
from stobu.types.struct import StructRecord, StructsData, StructType
from stobu.utils.dicts import dict_sorted
from stobu.utils.log import logger
from stobu.utils.strings import translate_by_dict


__all__ = (
        'structs_data_from',
        'outputs_data_from_structs_data',
        )


# Define Constants
PROC = 'BUILD STRUCT'


ACT_TITLES = [
        ActDataType.BOOK_TITLE,
        ActDataType.CHAPTER_TITLE,
        ActDataType.EPISODE_TITLE,
        ActDataType.SCENE_TITLE,
        ActDataType.SCENE_HEAD,
        ]


# Main
def structs_data_from(actions_data: ActionsData, tags: dict) -> StructsData:
    assert isinstance(actions_data, ActionsData)
    assert isinstance(tags, dict)

    logger.debug(msg.PROC_START.format(proc=PROC))

    base_data = _base_structs_data_from(actions_data)

    updated = update_data_tags(base_data, tags)

    eliminated = _eliminate_empty_records(updated)

    logger.debug(msg.PROC_SUCCESS.format(proc=PROC))
    return StructsData(eliminated)


def outputs_data_from_structs_data(structs_data: StructsData, tags: dict) -> OutputsData:
    assert isinstance(structs_data, StructsData)
    assert isinstance(tags, dict)

    _PROC = f"{PROC}: convert outputs data"
    logger.debug(msg.PROC_START.format(proc=_PROC))

    formatted = format_structs_data(structs_data)

    translated = translate_tags_text_list(formatted, tags)

    logger.debug(msg.PROC_SUCCESS.format(proc=_PROC))
    return OutputsData(translated)


def update_data_tags(origin_data: list, tags: dict) -> list:
    assert isinstance(origin_data, list)
    assert isinstance(tags, dict)

    tmp = []
    callings = get_calling_tags()

    for record in origin_data:
        assert isinstance(record, StructRecord)
        if record.type is StructType.ACTION:
            tmp.append(_update_tags_action_record(record, tags, callings))
        elif StructType.SCENE_DATA is record.type:
            tmp.append(_update_tags_scene_data_record(record, tags))
        else:
            tmp.append(record)

    return tmp


# Private Functions
def _base_structs_data_from(actions_data: ActionsData) -> list:
    assert isinstance(actions_data, ActionsData)

    tmp = []
    cache = {
            'camera': None,
            'stage': None,
            'year': None,
            'date': None,
            'time': None,
            }
    def reset_cache():
        cache['camera'] = None
        cache['stage'] = None
        cache['year'] = None
        cache['date'] = None
        cache['time'] = None

    for record in actions_data.get_data():
        assert isinstance(record, ActionRecord)
        if record.type is ActType.DATA:
            if record.subtype in ACT_TITLES:
                tmp.append(_record_as_title_from(record))
            elif ActDataType.SCENE_START is record.subtype:
                tmp.append(_record_as_scene_data_from(
                    cache['camera'], cache['stage'], cache['year'],
                    cache['date'], cache['time']))
            elif ActDataType.SCENE_END is record.subtype:
                reset_cache()
            elif ActDataType.SCENE_CAMERA is record.subtype:
                cache['camera'] = record
            elif ActDataType.SCENE_STAGE is record.subtype:
                cache['stage'] = record
            elif ActDataType.SCENE_YEAR is record.subtype:
                cache['year'] = record
            elif ActDataType.SCENE_DATE is record.subtype:
                cache['date'] = record
            elif ActDataType.SCENE_TIME is record.subtype:
                cache['time'] = record
            elif ActDataType.COMMENT is record.subtype:
                tmp.append(_record_as_comment_from(record))
            elif ActDataType.BR is record.subtype:
                continue
            elif ActDataType.PARAGRAPH_START is record.subtype:
                continue
            elif ActDataType.PARAGRAPH_END is record.subtype:
                continue
            elif ActDataType.TEXT is record.subtype:
                tmp.append(_record_as_text_from(record))
            else:
                logger.warning(msg.ERR_FAIL_UNKNOWN_DATA.format(data=f"act data sub type in {PROC}"))
                continue
        elif record.type in NORMAL_ACTIONS:
            tmp.append(_record_as_action_from(record))
        elif record.type in [ActType.NONE, ActType.SAME]:
            # NOTE: SE?
            continue
        else:
            logger.warning(msg.ERR_FAIL_INVALID_DATA.format(data=f"act type in {PROC}"))
            continue

    return tmp


def _eliminate_empty_records(base_data: list) -> list:
    assert isinstance(base_data, list)

    tmp = []

    for record in base_data:
        assert isinstance(record, StructRecord)
        if record.type in [StructType.COMMENT, StructType.TEXT]:
            if StructType.COMMENT is record.type:
                if record.subject:
                    tmp.append(record)
            elif StructType.TEXT is record.type:
                if record.subject:
                    tmp.append(record)
            else:
                if record.desc:
                    tmp.append(record)
        else:
            tmp.append(record)

    return tmp


def _record_as_comment_from(record: ActionRecord):
    assert isinstance(record, ActionRecord)

    return StructRecord(
            StructType.COMMENT,
            ActType.DATA,
            record.subject,
            record.outline,
            record.note)


def _record_as_action_from(record: ActionRecord):
    assert isinstance(record, ActionRecord)

    return StructRecord(
            StructType.ACTION,
            record.type,
            record.subject,
            record.outline,
            record.note)


def _record_as_scene_data_from(camera: ActionRecord, stage: ActionRecord,
        year: ActionRecord, date: ActionRecord, time: ActionRecord) -> StructRecord:

    return StructRecord(
            StructType.SCENE_DATA,
            ActType.DATA,
            camera.subject,
            stage.subject,
            {'year': year.subject,
                'date': date.subject,
                'time': time.subject,
                })


def _record_as_text_from(record: ActionRecord) -> StructRecord:
    assert isinstance(record, ActionRecord)

    return StructRecord(
            StructType.TEXT,
            ActType.DO,
            record.subject,
            record.outline,
            record.note)


def _record_as_title_from(record: ActionRecord) -> StructRecord:
    assert isinstance(record, ActionRecord)

    return StructRecord(
            _title_type_of(record),
            ActType.DATA,
            record.subject,
            record.outline,
            record.note)


def _title_type_of(record: ActionRecord) -> StructType:
    assert isinstance(record, ActionRecord)

    if ActDataType.BOOK_TITLE is record.subtype:
        return StructType.TITLE_BOOK
    elif ActDataType.CHAPTER_TITLE is record.subtype:
        return StructType.TITLE_CHAPTER
    elif ActDataType.EPISODE_TITLE is record.subtype:
        return StructType.TITLE_EPISODE
    elif ActDataType.SCENE_TITLE is record.subtype:
        return StructType.TITLE_SCENE
    elif ActDataType.SCENE_HEAD is record.subtype:
        return StructType.TITLE_TEXT
    else:
        logger.warning(msg.ERR_FAIL_INVALID_DATA.format(data=f"title type in {PROC}"))
        return StructType.NONE


def _update_tags_action_record(record: StructRecord, tags: dict,
        callings: dict) -> StructRecord:
    assert isinstance(record, StructRecord)
    assert isinstance(tags, dict)
    assert isinstance(callings, dict)

    if record.subject in callings:
        calling = dict_sorted(callings[record.subject], True)
        return StructRecord(
            record.type,
            record.act,
            translate_by_dict(record.subject, tags, True),
            translate_by_dict(record.outline, calling),
            translate_by_dict(record.note, calling),
            )
    else:
        return record


def _update_tags_scene_data_record(record: StructRecord, tags: dict) -> StructRecord:
    assert isinstance(record, StructRecord)
    assert isinstance(tags, dict)

    year = str(record.note['year'])
    date = str(record.note['date'])
    time = str(record.note['time'])

    return StructRecord(
            record.type,
            record.act,
            translate_by_dict(record.subject, tags, True),
            translate_by_dict(record.outline, tags, True),
            {
                'year': translate_by_dict(year, tags, True),
                'date': translate_by_dict(date, tags, True),
                'time': translate_by_dict(time, tags, True),
            })
