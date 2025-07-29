from barfi.flow import Block


def get_parameters(parameter_text, type_converter=float):
    if "," in parameter_text:
        tune_flag = True
        return tune_flag, [type_converter(each) for each in parameter_text.split(",")]
    else:
        tune_flag = False
        return tune_flag, type_converter(parameter_text)


def create_node(node_name, node_func, outputs=["O"], inputs=["X", "y"], options={}):

    for i, each_output in enumerate(outputs):
        if each_output in inputs:
            outputs[i] = each_output + "'"

    node = Block(name=node_name)

    for each_input in inputs:
        node.add_input(name=each_input)

    for each_output in outputs:
        node.add_output(name=each_output)

    for each_option in options:
        node.add_option(name="text", type="display", value=each_option)
        node.add_option(
            name=each_option, type="input", value=str(options[each_option]["default"])
        )

    def compute_func(self):
        print(f"---{node_name}---")
        input_variables = []

        for each_input in self._inputs:
            (plp_setting, plp, X) = self.get_interface(name=each_input)
            input_variables.append(X)

        assert len(options) <= 1
        print(f"{node_func=}")
        print(f"{input_variables=}")
        print(f"{options=}")
        if len(options) == 0:
            output_variables = node_func(*input_variables)
        elif len(options) == 1:
            option = next(iter(options))
            # print(self.get_option(name=option))
            type_converter = options[option]["type"]
            tune_flag, parameters = get_parameters(
                self.get_option(name=option), type_converter
            )
            # parameters[option] = parameters_
            print("parameters", parameters)
            print("tune_flag", tune_flag)

            if not tune_flag:
                input_variables.append(parameters)
                output_variables = node_func(*input_variables)
            else:
                plp_setting["tune_flag"] = tune_flag
                output_variables = node_func(*input_variables, parameters=parameters)
        print(f"{output_variables=}")
        if len(outputs) == 1:
            self.set_interface(
                name=outputs[0], value=(plp_setting, plp, output_variables)
            )
        elif len(outputs) == 2:
            for i, each_output in enumerate(outputs):
                self.set_interface(
                    name=each_output, value=(plp_setting, plp, output_variables[i])
                )
        else:
            raise Warning("the number of outputs should be 1 or 2")
        print(outputs)
        print("----------")

    node.add_compute(compute_func)
    return node
