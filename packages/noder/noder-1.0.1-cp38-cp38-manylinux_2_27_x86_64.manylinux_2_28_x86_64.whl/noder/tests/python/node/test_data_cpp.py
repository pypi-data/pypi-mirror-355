import noder.tests.data as test_in_cpp

def test_hasString(): return test_in_cpp.hasString()

def test_isNone(): return test_in_cpp.isNone()

def test_isScalar(): return test_in_cpp.isScalar()

def test_expectedString(): return test_in_cpp.expectedString()

if __name__ == '__main__':
    test_isNone()