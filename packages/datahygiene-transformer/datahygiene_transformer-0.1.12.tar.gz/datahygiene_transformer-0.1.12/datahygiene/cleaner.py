# datahygiene/cleaner.py
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
import yaml
import json

class DataHygieneTransformer(BaseEstimator, TransformerMixin):
    def __init__(self, numeric_cols=None, cat_cols=None, fillna=True, drop_constant=True,
                 drop_high_cardinality=None, validate_schema=True, verbose=True, encode='onehot'):
        """
        Initialize the transformer with configuration options.
        - numeric_cols: list of numeric column names
        - cat_cols: list of categorical column names
        - fillna: whether to fill missing values
        - drop_constant: whether to drop columns with no variance
        - drop_high_cardinality: threshold to drop columns with too many unique values
        - validate_schema: placeholder for optional schema checks
        - verbose: toggle for debug prints (future use)
        - encode: method to encode categorical features ('onehot', 'ordinal', or None)
        """
        self.numeric_cols = numeric_cols
        self.cat_cols = cat_cols
        self.fillna = fillna
        self.drop_constant = drop_constant
        self.drop_high_cardinality = drop_high_cardinality
        self.validate_schema = validate_schema
        self.verbose = verbose
        self.encode = encode

        # Internal state saved during fit
        self.constant_cols_ = []
        self.high_card_cols_ = []
        self.fill_medians_ = {}           # For numeric columns
        self.all_categories_ = {}         # For categorical columns
        self.ordinal_maps_ = {}           # For ordinal encoding

    @classmethod
    def from_config(cls, filepath):
        """
        Create a transformer using a config file (YAML or JSON).
        """
        if filepath.endswith(".yaml") or filepath.endswith(".yml"):
            with open(filepath, "r") as f:
                config = yaml.safe_load(f)
        elif filepath.endswith(".json"):
            with open(filepath, "r") as f:
                config = json.load(f)
        else:
            raise ValueError("Unsupported config format. Use YAML or JSON.")
        return cls(**config)

    def fit(self, X, y=None):
        """
        Learn medians, categories, and which columns to drop based on the training data.
        """
        X = X.copy()

        # Automatically detect columns if not provided
        if self.numeric_cols is None:
            self.numeric_cols = X.select_dtypes(include=['number']).columns.tolist()
        if self.cat_cols is None:
            self.cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()

        # Save medians for numeric imputation
        for col in self.numeric_cols:
            if self.fillna:
                self.fill_medians_[col] = X[col].median()

        # Save known categories and encoding maps for categorical columns
        for col in self.cat_cols:
            X[col] = X[col].astype("category")
            if self.fillna:
                X[col] = X[col].cat.add_categories('Unknown')
                X[col] = X[col].fillna('Unknown')
            cats = sorted([str(v) for v in X[col].dropna().unique()])
            self.all_categories_[col] = cats
            if self.encode == 'ordinal':
                self.ordinal_maps_[col] = {cat: idx for idx, cat in enumerate(cats)}

        # Identify constant columns
        if self.drop_constant:
            self.constant_cols_ = [col for col in X.columns if X[col].nunique(dropna=False) <= 1]

        # Identify high-cardinality columns
        if self.drop_high_cardinality:
            self.high_card_cols_ = [col for col in self.cat_cols if X[col].nunique() > self.drop_high_cardinality]

        return self

    def transform(self, X):
        X = X.copy()

        # Fill numeric columns and enforce dtype
        for col in self.numeric_cols:
            if self.fillna:
                X[col] = X[col].fillna(self.fill_medians_.get(col, 0))
            X[col] = X[col].astype(float)

        # Align and fill categorical columns
        for col in self.cat_cols:
            X[col] = X[col].astype("category")
            if self.fillna:
                if 'Unknown' not in X[col].cat.categories:
                    X[col] = X[col].cat.add_categories('Unknown')
                X[col] = X[col].fillna('Unknown')
            if col in self.all_categories_:
                X[col] = X[col].cat.set_categories(self.all_categories_[col])

        # Drop columns as needed
        if self.drop_constant:
            X.drop(columns=self.constant_cols_, inplace=True, errors='ignore')

        if self.drop_high_cardinality:
            X.drop(columns=self.high_card_cols_, inplace=True, errors='ignore')

        # Encode categorical columns
        if self.encode == 'ordinal':
            for col in self.cat_cols:
                if col in X.columns:
                    mapped = X[col].map(self.ordinal_maps_.get(col, {}))
                    # Convert to object if categorical
                    if pd.api.types.is_categorical_dtype(mapped):
                        # Step 1: convert categorical to integer codes (int dtype, with -1 for NaN)
                        codes = mapped.cat.codes

                        # Step 2: replace -1 (missing) with np.nan so we can fillna safely
                        codes = codes.replace(-1, np.nan)

                        # Step 3: fillna with -1 (or any sentinel you want)
                        codes = codes.fillna(-1).astype(int)

                        # Ensure -1 is a valid category
                        if -1 not in mapped.cat.categories:
                            mapped = mapped.cat.add_categories([-1])

                        mapped = codes  # assign back
                    else:
                        mapped = mapped.fillna(-1)

                    X[col] = mapped

        elif self.encode == 'onehot':
            X = pd.get_dummies(X, columns=self.cat_cols, dummy_na=False)

        return X

