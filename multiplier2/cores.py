import sys
sys.path.append("..")

from ip_generator.pipeliner import Input, Output, Component
from ip_generator.float import single_to_float, float_to_single
from ip_generator.float import double_to_float, float_to_double
import ip_generator.float
import ip_generator.pipeliner


#mul
mul = Component()
Output(mul, 'mul_z', 
    float_to_single(
        single_to_float(Input(mul, 32, 'mul_a')).__mul__(single_to_float(Input(mul, 32, 'mul_b')), mul)
    )
)


#mul
double_mul = Component()
Output(double_mul, 'double_mul_z', 
    float_to_double(
        double_to_float(Input(double_mul, 64, 'double_mul_a')).__mul__(
        double_to_float(Input(double_mul, 64, 'double_mul_b')), double_mul)
    )
)





