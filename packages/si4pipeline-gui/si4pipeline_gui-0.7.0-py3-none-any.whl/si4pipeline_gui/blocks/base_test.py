import pickle
import traceback
from pathlib import Path
from importlib.resources import files, as_file

import numpy as np
import pandas as pd


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
        local_path = Path(__file__).resolve().parent.parent / rel_path
        if not local_path.exists():
            raise FileNotFoundError(f"Resource not found locally: {local_path}")
        return local_path



class BaseTest:
    DATASET_META = {
        "prostate_cancer": (
            "dataset/prostate_cancer.pkl",
            ["lcavol", "lweight", "age", "lbph",
             "svi", "lcp", "gleason", "pgg45"],
        ),
        "red_wine": (
            "dataset/red_wine.pkl",
            ["fixed_acidity", "volatile_acidity", "citric_acid", "residual_sugar",
             "chlorides", "free_sulfur_dioxide", "total_sulfur_dioxide",
             "density", "pH", "sulphates", "alcohol"],
        ),
        "concrete": (
            "dataset/concrete.pkl",
            ["cement", "blast_furnace_slag", "fly_ash", "water",
             "superplasticizer", "coarse_aggregate", "fine_aggregate", "age"],
        ),
        "abalone": (
            "dataset/abalone.pkl",
            ["length", "diameter", "height", "whole_weight",
             "shucked_weight", "viscera_weight", "shell_weight"],
        ),
    }

    def __init__(self, st):
        self.st = st

    def _load_dataset(self, key):
        file_rel, features = self.DATASET_META[key]
        file_path: Path = _resolve_resource(file_rel)
        with file_path.open("rb") as f:
            X, y = pickle.load(f)
        return X, y, features

    def perform_inference(self, block):
        print("perform inference!")

        plp_setting, pipeline = self.make_pipeline(block)
        print("pipeline:", pipeline)
        try:
            if self.st.session_state.dataset == "random":
                n, p = 100, 10
                rng = np.random.default_rng(0)
                X = rng.normal(size=(n, p))
                y = rng.normal(size=n)
                num_missing = rng.binomial(n, 0.03)
                mask = rng.choice(n, num_missing, replace=False)
                y[mask] = np.nan
                sigma = 1.0
                features = [f"Feature {i+1}" for i in range(p)]

            elif self.st.session_state.dataset == "uploaded":
                X, y, features = self.st.session_state.uploaded_dataset
                sigma = None

            elif self.st.session_state.dataset in self.DATASET_META:
                X, y, features = self._load_dataset(self.st.session_state.dataset)
                sigma = None

            else:
                raise Warning("unknown dataset")
            
            if plp_setting["tune_flag"]:
                pipeline.tune(
                    X, y, num_folds=self.st.session_state.cv, random_state=0
                )

            if sigma is not None:
                M, p_list = pipeline.inference(X, y, sigma)
            else:
                M, p_list = pipeline.inference(X, y)

            print("Inference results are :\n")
            for each_feature, p_value in zip(M, p_list):
                print(
                    f'{features[each_feature]}:\np-value is {p_value:.6f}, \
                        {"significant" if p_value <= 0.05 else "not significant"}\n'
                )

            results = []
            for each_feature, p_value in zip(M, p_list):
                significance_status = (
                    "significant" if p_value <= 0.05 else "not significant"
                )
                result = {
                    "Feature": features[each_feature],
                    "p-value": round(p_value, 6),
                    "Significance": significance_status,
                }
                results.append(result)
            results_df = pd.DataFrame(results)
            self.st.session_state["results_df"] = results_df

        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()

    def make_pipeline(self2, self):
        raise NotImplementedError("make_pipeline method is not implemented")
