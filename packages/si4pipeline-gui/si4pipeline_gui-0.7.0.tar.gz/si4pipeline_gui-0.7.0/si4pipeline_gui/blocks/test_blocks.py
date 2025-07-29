from barfi.flow import Block

from .base_test import BaseTest


class Test(BaseTest):
    def make_pipeline(self, block):
        (plp_setting, plp, M) = block.get_interface(name="M")
        print("M:", M)
        pipeline = plp.construct_pipelines(output=M)
        print("pipeline!:", pipeline)
        return plp_setting, pipeline


class TestWithMultiPipelines(BaseTest):
    def make_pipeline(self, block):
        (plp_setting, plp, M1) = block.get_interface(name="M1")
        (plp_setting, plp, M2) = block.get_interface(name="M2")
        manager_op1_mul = plp.construct_pipelines(output=M1)
        manager_op2_mul = plp.construct_pipelines(output=M2)
        manager = manager_op1_mul | manager_op2_mul

        plp_setting["tune_flag"] = True
        return plp_setting, manager


def get_test_blocks(st):
    test = Block(name="Test")
    test.add_input(name="M")
    test.add_compute(Test(st).perform_inference)

    test_with_multi_pipeline = Block(name="Test with Multi Pipelines")
    test_with_multi_pipeline.add_input(name="M1")
    test_with_multi_pipeline.add_input(name="M2")
    test_with_multi_pipeline.add_compute(TestWithMultiPipelines(st).perform_inference)

    return [test, test_with_multi_pipeline]
