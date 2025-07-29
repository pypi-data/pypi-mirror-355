import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from .preprocessing import StandardScaler, add_intercept  # Import your custom classes


def preprocess_ecological_dataset(filepath="ecological_health_dataset.csv"):
    """
    Load and preprocess the ecological health dataset using custom preprocessing tools.
    
    Parameters:
    -----------
    filepath : str
        Path to the dataset CSV file
    
    Returns:
    --------
    X : numpy.ndarray
        Preprocessed feature matrix
    y : numpy.ndarray
        Target variable (Biodiversity_Index)
    feature_names : list
        Names of the features after preprocessing
    """
    print("Loading and preprocessing the ecological health dataset...")
    df = pd.read_csv(filepath)

    # Display basic information
    print(f"Dataset shape: {df.shape}")
    print(f"Target variable distribution:\n{df['Biodiversity_Index'].value_counts().sort_index().head()}")

    # Remove Timestamp column if exists
    if 'Timestamp' in df.columns:
        df = df.drop(columns=['Timestamp'])

    # Handle missing values
    missing_values = df.isnull().sum()
    if missing_values.sum() > 0:
        print("Missing values detected. Filling with appropriate values...")
        numeric_cols = df.select_dtypes(include=['number']).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        categorical_cols = ['Pollution_Level', 'Ecological_Health_Label']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].mode()[0])

    # Identify categorical columns
    categorical_cols = [col for col in ['Pollution_Level', 'Ecological_Health_Label'] if col in df.columns]

    # Prepare transformers
    transformers = []
    numeric_cols = [col for col in df.columns if col not in categorical_cols + ['Biodiversity_Index']]
    if numeric_cols:
        transformers.append(('num', StandardScaler(), numeric_cols))
    if categorical_cols:
        transformers.append(('cat', OneHotEncoder(drop='first'), categorical_cols))

    preprocessor = ColumnTransformer(transformers=transformers, remainder='drop')

    # Extract features and target
    X = df.drop(columns=['Biodiversity_Index'])
    y = df['Biodiversity_Index'].values

    # Fit and transform features
    X_processed = preprocessor.fit_transform(X)

    # Add intercept if needed (optional, depending on model)
    # X_processed = add_intercept(X_processed)

    # Get feature names after preprocessing
    feature_names = []
    if numeric_cols:
        feature_names.extend(numeric_cols)
    if categorical_cols:
        ohe = preprocessor.named_transformers_['cat']
        for i, col in enumerate(categorical_cols):
            categories = ohe.categories_[i][1:]  # Skip first category due to drop='first'
            feature_names.extend([f"{col}_{cat}" for cat in categories])

    print(f"Processed features shape: {X_processed.shape}")
    print(f"Target variable shape: {y.shape}")

    return X_processed, y, feature_names