from __future__ import print_function

from energyPATHWAYS.data_object import StringMap

if __name__ == "__main__":
    mapper = StringMap.getInstance()

    lst = ('foo', 'bar', 'baz', 'bing', 'bang', 'bong')
    ids = map(mapper.store, lst)
    print('IDs for %s: %s' % (lst, ids))
    print("txt_to_id:", mapper.txt_to_id)
    print("id_to_txt:", mapper.id_to_txt)
    txt = map(mapper.get_txt, ids)
    print('Strings for %s: %s' % (ids, txt))

    try:
        print("ID for 'huh?'")
        mapper.get_id('huh?')
    except KeyError:
        print('KeyError (as expected)')

    print("ID for 'huh?'", mapper.get_id('huh?', raise_error=False))
