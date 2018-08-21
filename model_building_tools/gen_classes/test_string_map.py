from __future__ import print_function

from energyPATHWAYS.data_object import StringMap

if __name__ == "__main__":
    mapper = StringMap.getInstance()

    lst = ('foo', 'bar', 'baz', 'bing', 'bang', 'bong')
    ids = map(mapper.store, lst)
    print('IDs for %s: %s' % (lst, ids))
    print("text_to_id:", mapper.text_to_id)
    print("id_to_text:", mapper.id_to_text)
    text = map(mapper.get_text, ids)
    print('Strings for %s: %s' % (ids, text))

    try:
        print("ID for 'huh?'")
        mapper.get_id('huh?')
    except KeyError:
        print('KeyError (as expected)')

    print("ID for 'huh?'", mapper.get_id('huh?', raise_error=False))
