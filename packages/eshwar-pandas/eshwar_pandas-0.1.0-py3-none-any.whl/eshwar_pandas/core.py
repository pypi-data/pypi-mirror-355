import pandas as pd

class EshwarPandas:
    def __init__(self):
        self.df = None

    def load_csv(self, file_path):
        self.df = pd.read_csv(file_path)
        print(f"CSV loaded with {len(self.df)} rows and {len(self.df.columns)} columns")

    def preview(self, n=5):
        if self.df is not None:
            return self.df.head(n)
        raise ValueError("No CSV loaded. Please load a CSV first.")

    def data_types(self):
        if self.df is not None:
            return self.df.dtypes
        raise ValueError("No CSV loaded. Please load a CSV first.")
