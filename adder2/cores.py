import sys
sys.path.append("..")

from ip_generator.pipeliner import Input, Output, Component
from ip_generator.float import single_to_float, float_to_single
from ip_generator.float import double_to_float, float_to_double
import ip_generator.float
import ip_generator.pipeliner


#add
add = Component()
Output(add, 'add_z', 
    float_to_single(
        single_to_float(Input(add, 32, 'add_a')) 
        + 
        single_to_float(Input(add, 32, 'add_b'))
    )
)


#add
double_add = Component()
Output(double_add, 'double_add_z', 
    float_to_double(
        double_to_float(Input(double_add, 64, 'double_add_a')) 
        + 
        double_to_float(Input(double_add, 64, 'double_add_b'))
    )
)

