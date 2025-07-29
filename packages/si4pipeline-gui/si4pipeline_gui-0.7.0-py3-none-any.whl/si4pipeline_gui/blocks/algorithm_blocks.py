from .node_factory import create_node


def get_algorithm_blocks(plp):
    mean_value_imputation = create_node(
        "MVI: Mean Value Imputation",
        plp.mean_value_imputation,
        outputs=["y'"],
        inputs=["X", "y"],
    )
    regression_imputation = create_node(
        "MVI: Regression Imputation",
        plp.definite_regression_imputation,
        outputs=["y'"],
        inputs=["X", "y"],
    )
    soft_ipod = create_node(
        "OD: Soft IPOD",
        plp.soft_ipod,
        outputs=["O"],
        inputs=["X", "y"],
        options={"penalty coefficient": {"default": 0.015, "type": float}},
    )
    cook_distance = create_node(
        "OD: Cook Distance",
        plp.cook_distance,
        outputs=["O"],
        inputs=["X", "y"],
        options={"penalty coefficient": {"default": 3.0, "type": float}},
    )
    remove_outliers = create_node(
        "Remove Outliers",
        plp.remove_outliers,
        outputs=["X", "y"],
        inputs=["X", "y", "O"],
    )
    marginal_screening = create_node(
        "FS: Marginal Screening",
        plp.marginal_screening,
        outputs=["M"],
        inputs=["X", "y"],
        options={"number of features": {"default": 5, "type": int}},
    )
    stepwise_feature_selection = create_node(
        "FS: Stepwise Feature Selection",
        plp.stepwise_feature_selection,
        outputs=["M"],
        inputs=["X", "y"],
        options={"number of features": {"default": 3, "type": int}},
    )
    lasso = create_node(
        "FS: Lasso",
        plp.lasso,
        outputs=["M"],
        inputs=["X", "y"],
        options={"penalty coefficient": {"default": 0.08, "type": float}},
    )
    extract_features = create_node(
        "Feature Extraction", plp.extract_features, outputs=["X"], inputs=["X", "M"]
    )
    union = create_node("Union", plp.union, outputs=["M"], inputs=["M1", "M2"])
    intersection = create_node(
        "Intersection", plp.intersection, outputs=["M"], inputs=["M1", "M2"]
    )

    return [
        mean_value_imputation,
        regression_imputation,
        soft_ipod,
        cook_distance,
        remove_outliers,
        marginal_screening,
        stepwise_feature_selection,
        lasso,
        extract_features,
        union,
        intersection,
    ]
