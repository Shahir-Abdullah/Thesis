import sys
sys.path.append("..")

from ip_generator.pipeliner import Input, Output, Component
from ip_generator.float import single_to_float, float_to_single
from ip_generator.float import double_to_float, float_to_double
import ip_generator.float
import ip_generator.pipeliner

#divider
div = Component()
Output(div, 'div_z', 
    float_to_single(
        single_to_float(Input(div, 32, 'div_a')) 
        / 
        single_to_float(Input(div, 32, 'div_b'))
    )
)


#div
double_div = Component()
Output(double_div, 'double_div_z', 
    float_to_double(
        double_to_float(Input(double_div, 64, 'double_div_a')) 
        / 
        double_to_float(Input(double_div, 64, 'double_div_b'))
    )
)




