import logging
from rapidfuzz import process, fuzz, utils

logger = logging.getLogger(__name__)


def find_fuzzy_item(input_word, search_array, threshold=80, error=True):
    # Use the built-in 'process' function to find the closest match
    search_array = list(set(search_array))

    best_match = process.extract(input_word, search_array, scorer=fuzz.WRatio, processor=utils.default_process)
    best_match = best_match[0]
    confidence = best_match[1]

    if confidence < threshold:
        if error:
            raise ValueError(
                f'Input word: {input_word} | '
                f'Closest word: {best_match[0]} | '
                f'{confidence} was less than threshold ({threshold}) | '
                f'not found in {search_array}')
        else:
            logger.error(
                f'Input word: {input_word} | '
                f'Closest word: {best_match[0]} | '
                f'{confidence} was less than threshold ({threshold}) | '
                f'not found in {search_array}')
            return None

    return best_match[0]
