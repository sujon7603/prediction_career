import pandas as pd
import os


def load_data(file_path):
    df = pd.read_csv(file_path)
    return df

def clean_data(df):
    # remove duplicate rows
    df = df.drop_duplicates()

    # remove rows where career is missing
    df = df.dropna(subset=["career"])

    return df


def prepare_features(df):
    x = df.drop("career", axis=1)
    y = df["career"]

    return x, y

if __name__ == "__main__":

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
    file_path = os.path.join(
        BASE_DIR,
        "data",
        "career_dataset.csv"
    )

    df = load_data(file_path)

    print("Original Dataset : ")
    print(df.head())

    df = clean_data(df)

    print("\n Dataset After Cleaning : ")
    print(df.head())

    print("\n Dataset Shape : ")
    print(df.shape)

    x, y = prepare_features(df)

    print("\n Features : ")
    print(x.columns.tolist())

    print("\n Target : ")
    print(y.head())