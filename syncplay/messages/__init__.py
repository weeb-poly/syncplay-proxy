# coding:utf8
import logging

from .. import constants

from . import messages_en
from . import messages_ru
from . import messages_de
from . import messages_it
from . import messages_es
from . import messages_pt_BR
from . import messages_pt_PT

messages = {
    "en": messages_en.en,
    "ru": messages_ru.ru,
    "de": messages_de.de,
    "it": messages_it.it,
    "es": messages_es.es,
    "pt_BR": messages_pt_BR.pt_BR,
    "pt_PT": messages_pt_PT.pt_PT,
    "CURRENT": None
}


def getLanguages():
    langList = {}
    for lang in messages:
        if lang != "CURRENT":
            langList[lang] = getMessage("LANGUAGE", lang)
    return langList


def setLanguage(lang):
    messages["CURRENT"] = lang


def getMissingStrings():
    missingStrings = ""
    for lang in messages:
        if lang != "en" and lang != "CURRENT":
            for message in messages["en"]:
                if message not in messages[lang]:
                    missingStrings += f"({lang}) Missing: {message}\n"
            for message in messages[lang]:
                if message not in messages["en"]:
                    missingStrings += f"({lang}) Unused: {message}\n"

    return missingStrings


def getInitialLanguage():
    try:
        import locale
        initialLanguage = locale.getdefaultlocale()[0].split("_")[0]
        if initialLanguage not in messages:
            initialLanguage = constants.FALLBACK_INITIAL_LANGUAGE
    except:
        initialLanguage = constants.FALLBACK_INITIAL_LANGUAGE
    return initialLanguage


def isValidLanguage(language):
    return language in messages


def getMessage(type_, locale=None) -> str:
    if not constants.SHOW_TOOLTIPS:
        if "-tooltip" in type_:
            return ""

    if not isValidLanguage(messages["CURRENT"]):
        setLanguage(getInitialLanguage())

    lang = messages["CURRENT"]
    if locale and locale in messages:
        if type_ in messages[locale]:
            return str(messages[locale][type_])
    if lang and lang in messages:
        if type_ in messages[lang]:
            return str(messages[lang][type_])
    if type_ in messages["en"]:
        return str(messages["en"][type_])
    else:
        logging.warning(f"Cannot find message '{type_}'!")
        # return f"!{type_}"  # TODO: Remove
        raise KeyError(type_)
