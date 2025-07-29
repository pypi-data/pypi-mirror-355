from __future__ import annotations
from pathlib import Path
import os
import shutil
import importlib
from importlib.resources import files, as_file

import pandas as pd
import streamlit as st
from barfi.flow import SchemaManager
from barfi.flow.streamlit import st_flow
from barfi.flow import ComputeEngine
import si4pipeline as plp



def _flex_import(modpath: str, fallback: str):
    try:
        return importlib.import_module(modpath)
    except ModuleNotFoundError:
        return importlib.import_module(fallback)


get_algorithm_blocks = _flex_import(
    "si4pipeline_gui.blocks.algorithm_blocks", "blocks.algorithm_blocks"
).get_algorithm_blocks
get_dataset_loader_blocks = _flex_import(
    "si4pipeline_gui.blocks.load_blocks", "blocks.load_blocks"
).get_dataset_loader_blocks
get_test_blocks = _flex_import(
    "si4pipeline_gui.blocks.test_blocks", "blocks.test_blocks"
).get_test_blocks

load_blocks = get_dataset_loader_blocks(st, plp)
algorithm_blocks = get_algorithm_blocks(plp)
test_blocks = get_test_blocks(st)

base_blocks = load_blocks + algorithm_blocks + test_blocks


def _resolve_resource(rel_path: str) -> Path:
    """
    rel_path: e.g. 'schemas.barfi'  or 'dataset/abalone.pkl'
    """
    try:
        with as_file(files("si4pipeline_gui") / rel_path) as p:
            if not p.exists():
                raise FileNotFoundError(f"Resource not found in package: {rel_path}")
            return p
    except Exception:
        local_path = Path(__file__).resolve().parent / rel_path
        if not local_path.exists():
            raise FileNotFoundError(f"Resource not found locally: {rel_path}")
        return local_path


def _init_user_schema_file() -> Path:
    SCHEMA_FILENAME = "schemas.barfi"
    user_home = Path(os.getenv("SI4PIPELINE_HOME", Path.home() / ".si4pipeline_gui"))
    user_home.mkdir(parents=True, exist_ok=True)
    target = user_home / SCHEMA_FILENAME

    if not target.exists():
        try:
            source = _resolve_resource(SCHEMA_FILENAME)
            shutil.copyfile(source, target)
        except Exception:
            target = _resolve_resource(SCHEMA_FILENAME)

    return target

SCHEMA_FILE = _init_user_schema_file()
my_schema_manager = SchemaManager(str(SCHEMA_FILE))
# my_schema_manager = SchemaManager("./schemas.barfi")

@st.dialog("Enter a pipeline name")
def save_dialog(flow_schema, manager):
    name = st.text_input("Pipeline name", key="schema_input")
    if st.button("Save"):
        try:
            manager.save_schema(name, flow_schema)
            st.session_state["selected_pipeline_name"] = name
            st.toast(f"Pipeline '{name}' has been saved")
            st.rerun()
        except ValueError:
            st.error("A pipeline with this name already exists. Please choose another.")


def main():
    st.set_page_config(page_icon="🍍", page_title="SI4PIPELINE", layout="wide")

    st.title("SI4PIPELINE")

    st.sidebar.title("Settings")
    st.sidebar.markdown("---")
    st.sidebar.subheader("Hyperparameters")
    cv = st.sidebar.slider("Number of folds in cross-validation:", 0, 10, 5)
    if "cv" not in st.session_state:
        st.session_state.cv = cv

    st.sidebar.markdown("---")
    st.sidebar.subheader("Manage Pipelines")
    if my_schema_manager.schema_names:
        to_delete = st.sidebar.selectbox(
            "Pipeline to delete",
            my_schema_manager.schema_names,
            key="delete_pipeline_select",
        )
        if st.sidebar.button("Delete pipeline", key="delete_pipeline_btn"):
            my_schema_manager.delete_schema(to_delete)
            if st.session_state.get("selected_pipeline_name") == to_delete:
                remaining = my_schema_manager.schema_names
                st.session_state["selected_pipeline_name"] = (
                    remaining[0] if remaining else None
                )
            st.toast(f"Pipeline '{to_delete}' deleted")
            st.rerun()
    else:
        st.sidebar.info("No saved pipeline yet.")

    # load data
    st.header("STEP1: Upload data")
    _, col1, col2 = st.columns([1, 8, 7])
    with col1:
        uploaded_file = st.file_uploader("Upload your own data", type="csv")
        if uploaded_file is not None:
            header_exists = st.checkbox("The file have a header", value=True)
            if header_exists:
                data = pd.read_csv(uploaded_file)
            else:
                data = pd.read_csv(uploaded_file, header=None)
            default_target_column = data.columns[-1]
            target_column = st.text_input(
                "Target column name:", value=default_target_column
            )
            y = data[target_column].values
            X = data.drop(columns=[target_column]).values
            features = data.drop(columns=[target_column]).columns
            st.session_state.dataset = "uploaded"
            st.session_state.uploaded_dataset = [X, y, features]
    with col2:
        # if st.checkbox('or select existing dataset'):
        if uploaded_file is None:
            existing_data_options = [
                "-",
                "random",
                "prostate_cancer",
                "red_wine",
                "concrete",
                "abalone",
            ]
            # デモ用のデータセットを選択
            selected_dataset = st.selectbox(
                "Or select a demo dataset:", existing_data_options
            )
            if selected_dataset != "-":
                st.session_state.dataset = selected_dataset
    if uploaded_file:
        _, col1 = st.columns([1, 15])
        with col1:
            with st.expander("Show data"):
                st.dataframe(data, height=300)

    # load and define pipeline
    st.header("STEP2: Define and execute pipeline")
    _, col1, col2 = st.columns([1, 8, 7])
    with col1:
        st.write("Define your data processing pipeline")
        # st.write('You can create blocks by right-clicking and connect them to create a pipeline.')
        # st.write('You can also set parameters for each block.')
        # st.write('After defining the pipeline, click the "Execute" button to perform the analysis.')
        # st.write('The results will be displayed in the next section.')
    with col2:
        selected_pipeline_name = st.selectbox(
            "Or select a pre-defined pipeline:", my_schema_manager.schema_names, key="selected_pipeline_name"
        )

    _, col1 = st.columns([1, 15])

    with col1:
        if selected_pipeline_name is None:
            barfi_result = st_flow(
                blocks=base_blocks,
            )
        else:
            my_flow_schema = my_schema_manager.load_schema(
                schema_name=selected_pipeline_name
            )
            barfi_result = st_flow(
                blocks=base_blocks,
                editor_schema=my_flow_schema,
            )

    if barfi_result.command == "execute":
        engine = ComputeEngine(base_blocks)
        flow_schema = barfi_result.editor_schema
        engine.execute(flow_schema)

    if barfi_result.command == "save":
        save_dialog(barfi_result.editor_schema, my_schema_manager)

    # inference results
    st.header("STEP3: Inference results")
    _, col1 = st.columns([1, 15])
    with col1:
        if "results_df" not in st.session_state:
            if "executed" in st.session_state:
                st.error(
                    "The analysis has failed.\n\
                         Please check the pipeline structure and the dataset format."
                )
            else:
                st.write("(No analysis has been performed yet.)")
        else:
            def highlight_significant(row):
                color = (
                    "background-color: lightgreen"
                    if row["Significance"] == "significant"
                    else "background-color: lightblue"
                )
                return [color] * len(row)

            styled_df = st.session_state["results_df"].style.apply(
                highlight_significant, axis=1
            )
            st.dataframe(styled_df)


if __name__ == "__main__":
    main()
