import contextlib, time, cProfile, StringIO, pstats

@contextlib.contextmanager
def profile():
    pr = cProfile.Profile()
    pr.enable()
    yield
    pr.disable()
    s = StringIO.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats()
    # uncomment this to see who's calling what
    # ps.print_callers()
    print s.getvalue()

@contextlib.contextmanager
def timer(prefix='time'):
    start = time.time()
    yield
    end = time.time()
    print '%s: %0.4fs' % (prefix, end - start)