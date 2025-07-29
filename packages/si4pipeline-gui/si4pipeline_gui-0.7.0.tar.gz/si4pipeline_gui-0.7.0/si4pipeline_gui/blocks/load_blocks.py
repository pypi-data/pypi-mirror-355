from barfi.flow import Block


def get_dataset_loader_blocks(st, plp):
    load = Block(name="Dataset Loader")
    load.add_output(name="X")
    load.add_output(name="y")

    def load_func(self):
        st.session_state["executed"] = True
        if "results_df" in st.session_state:
            del st.session_state["results_df"]

        print("load")
        X, y = plp.initialize_dataset()
        plp_setting = {}
        plp_setting["tune_flag"] = False
        self.set_interface(name="X", value=(plp_setting, plp, X))
        self.set_interface(name="y", value=(plp_setting, plp, y))

    load.add_compute(load_func)
    return [load]
