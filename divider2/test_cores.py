import sys
sys.path.append("..")

import subprocess
import random
import cores
import struct
from numpy import float32
from itertools import product
from random import randint
from multiprocessing import Process
from math import isnan, isinf
import csv 
import datetime 
def trace(response, n):
    for name, values in response.iteritems():
        print name, values[n]

def asfloat(x):
    string = ""
    for i in range(4):
        byte = x >> 24
        byte &= 0xff
        string += chr(byte)
        x <<= 8
    return struct.unpack(">f", string)[0]

def failure(a, b, actual, expected):
    print "a        b        actual   expected"
    print "======== ======== ======== ========"
    print "%08x %08x %08x %08x fail"%(a, b, actual, expected)
    print "a", asfloat(a)
    print "b", asfloat(b)
    print "actual", asfloat(actual)
    print "expected", asfloat(expected)

def get_expected(core_name):
    subprocess.call("./reference_tests/"+core_name)
    inf = open("stim/%s_z_expected"%core_name)
    return [int(i) for i in inf]

def get_mantissa(x):
    return 0x7fffff & x

def get_exponent(x):
    return ((x & 0x7f800000) >> 23) - 127

def get_sign(x):
    return ((x & 0x80000000) >> 31)

def is_nan(x):
    return get_exponent(x) == 128 and get_mantissa(x) != 0

def is_inf(x):
    return get_exponent(x) == 128 and get_mantissa(x) == 0

def is_pos_inf(x):
    return is_inf(x) and not get_sign(x)

def is_neg_inf(x):
    return is_inf(x) and get_sign(x)

def match(x, y):
    return (
        (is_pos_inf(x) and is_pos_inf(y)) or
        (is_neg_inf(x) and is_neg_inf(y)) or
        (is_nan(x) and is_nan(y)) or
        (x == y)
        )

def test_convert(core_name, core, a):
    print "testing", core_name, "..."
    stimulus = {core_name+'_a':a}

    response = core.test(stimulus, name=core_name)
    actual = response[core_name+"_z"]
    expected = get_expected(core_name)

    n = 0
    for a, i, j in zip(a, actual, expected):
        if asfloat(a) < 0 and "to_unsigned" in core_name:
            result = True
        elif asfloat(a) > (2**32)-1 and "to_unsigned" in core_name:
            result = True
        elif asfloat(a) > (2**31)-1 and "to_int" in core_name:
            result = True
        elif asfloat(a) < -(2**31) and "to_int" in core_name:
            result = True
        elif isnan(asfloat(a)):
            result = True
        else:
            if(j != i):
                result = False
            else:
                result = True
        if not result:
            trace(response, n)
            print "input actual expected"
            print "%08x %08x %08x fail"%(a, i, j)
            print asfloat(a), asfloat(i), asfloat(j)
            sys.exit(1)
        n += 1


def test_binary(core_name, core, a, b):
    print "testing", core_name, "..."
    stimulus = {
        core_name+'_a':a, 
        core_name+'_b':b
    }

    response = core.test(stimulus, name=core_name)
    actual = response[core_name+"_z"]
    expected = get_expected(core_name)

    n = 0
    for a, b, i, j in zip(a, b, actual, expected):
        result = match(i, j)
	print("a : ", asfloat(a), " b : ", asfloat(b), " Result : ", asfloat(i), " Expected Result : ", asfloat(j), " Status =========> OK")
        if not result:
            print "%08x %08x %08x %08x fail"%(a, b, i, j)
            print "a:", asfloat(a)
            print "b:", asfloat(b)
            print "actual", asfloat(i)
            print "expected", asfloat(j)
            print n
            trace(response, n)
            #append failures to regression test file
            of = open("regression_tests", "a")
            of.write("%i %i\n"%(a, b))
            of.close()
            sys.exit(1)
        n += 1

def test_cores(stimulus_a, stimulus_b):
    binary_cores = {
         
        "div":cores.div
       
        
    }
    processes = []
    for core_name, core in binary_cores.iteritems():
        processes.append(
            Process(
                target=test_binary, 
                args=[core_name, core, stimulus_a, stimulus_b]
            )
        )

    
    for i in processes:
        i.daemon=True
        i.start()

    for i in processes:
        i.join()
        if i.exitcode:
            exit(i.exitcode)

###############################################################################
#tests start here
###############################################################################

count = 0

'''#regression tests
inf = open("regression_tests")
stimulus_a = []
stimulus_b = []
for line in inf.read().splitlines():
    a, b = line.strip().split()
    stimulus_a.append(int(a))
    stimulus_b.append(int(b))
test_cores(stimulus_a, stimulus_b)
count += len(stimulus_a)
print count, "vectors passed"
'''
with open('data_file.csv', mode='a') as data_file:
    data_writer = csv.writer(data_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    #regression tests
    stimulus_a = [0xaf860e03, 0x22cb525a, 0x40000000, 0x83e73d5c, 0xbf9b1e94, 0x34082401, 0x5e8ef81, 0x5c75da81, 0x2b017]
    stimulus_b = [0x0681db7f, 0xadd79efa, 0xC0000000, 0x1c800000, 0xc038ed3a, 0xb328cd45, 0x114f3db, 0x2f642a39, 0xff3807ab]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c = b-a  
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors regression tests passed in ", c.total_seconds(), " seconds")

    #corner cases
    special_values = [
            0x80000000, 0x00000000, 
            0x7f800000, 0xff800000, 
            0x7fc00000, 0xffc00000, 
            0x00000001, 0x00400000, 0x007fffff, 0x80000001,  0x80400000, 0x807fffff]
    vectors = list(product(special_values, special_values))
    stimulus_a = [a for a, b in vectors]
    stimulus_b = [b for a, b in vectors]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b-a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors corner cases passed in ", c.total_seconds(), " seconds")

    #edge cases
    stimulus_a = [0x80000000 for i in xrange(1000)]
    stimulus_b = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_a = [0x00000000 for i in xrange(1000)]
    stimulus_b = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x80000000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x00000000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_a = [0x7F800000 for i in xrange(1000)]
    stimulus_b = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_a = [0xFF800000 for i in xrange(1000)]
    stimulus_b = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x7F800000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0xFF800000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_a = [0x7FC00000 for i in xrange(1000)]
    stimulus_b = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_a = [0xFFC00000 for i in xrange(1000)]
    stimulus_b = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x7FC00000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0xFFC00000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x00000001 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x00400000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x007fffff for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x80000001 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x80400000 for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [0x807fffff for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

    stimulus_b = [randint(0, 1)<<31 | randint(0, 0x7fffff) for i in xrange(1000)]
    stimulus_a = [randint(0, 1<<32) for i in xrange(1000)]
    a = datetime.datetime.now()
    test_cores(stimulus_a, stimulus_b)
    b = datetime.datetime.now()
    c += b - a
    count += len(stimulus_a)
    data_writer.writerow([count, c.total_seconds()])
    print (count, "vectors edge cases passed in ", c.total_seconds(), " seconds")
    
    

