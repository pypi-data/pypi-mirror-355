from typing import Union, Optional, List, Tuple
import numpy as np
import pandas as pd

def validate_numeric_data(data: Union[np.ndarray, pd.DataFrame, pd.Series]) -> Union[np.ndarray, pd.DataFrame, pd.Series]:
    """
    Valide que les données sont numériques.
    
    Args:
        data: Données à valider
        
    Returns:
        Données validées
        
    Raises:
        TypeError: Si les données ne sont pas numériques
    """
    if isinstance(data, pd.DataFrame):
        if not all(pd.api.types.is_numeric_dtype(data[col]) for col in data.columns):
            raise TypeError("Toutes les colonnes doivent être numériques")
    elif isinstance(data, pd.Series):
        if not pd.api.types.is_numeric_dtype(data):
            raise TypeError("La série doit être numérique")
    elif isinstance(data, np.ndarray):
        if not np.issubdtype(data.dtype, np.number):
            raise TypeError("L'array doit être numérique")
    else:
        raise TypeError("Type de données non supporté")
    
    return data

def check_missing_values(data: Union[np.ndarray, pd.DataFrame, pd.Series]) -> Tuple[bool, Optional[pd.Series]]:
    """
    Vérifie la présence de valeurs manquantes.
    
    Args:
        data: Données à vérifier
        
    Returns:
        Tuple[bool, Optional[pd.Series]]: (présence de valeurs manquantes, statistiques des valeurs manquantes)
    """
    if isinstance(data, pd.DataFrame):
        missing_stats = data.isnull().sum()
        has_missing = missing_stats.any()
    elif isinstance(data, pd.Series):
        missing_stats = pd.Series({'missing': data.isnull().sum()})
        has_missing = missing_stats['missing'] > 0
    else:  # numpy array
        has_missing = np.isnan(data).any()
        missing_stats = None
    
    return has_missing, missing_stats

def validate_dimensions(data: Union[np.ndarray, pd.DataFrame], 
                       min_dim: int = 1, 
                       max_dim: int = 2) -> None:
    """
    Valide les dimensions des données.
    
    Args:
        data: Données à valider
        min_dim: Dimension minimale autorisée
        max_dim: Dimension maximale autorisée
        
    Raises:
        ValueError: Si les dimensions ne sont pas valides
    """
    if isinstance(data, pd.DataFrame):
        dim = 2
    else:  # numpy array
        dim = data.ndim
    
    if not min_dim <= dim <= max_dim:
        raise ValueError(f"Les données doivent avoir entre {min_dim} et {max_dim} dimensions")

def validate_sample_size(data: Union[np.ndarray, pd.DataFrame, pd.Series], 
                        min_size: int = 2) -> None:
    """
    Valide la taille de l'échantillon.
    
    Args:
        data: Données à valider
        min_size: Taille minimale requise
        
    Raises:
        ValueError: Si la taille de l'échantillon est insuffisante
    """
    if isinstance(data, pd.DataFrame):
        size = len(data)
    elif isinstance(data, pd.Series):
        size = len(data)
    else:  # numpy array
        size = data.shape[0]
    
    if size < min_size:
        raise ValueError(f"La taille de l'échantillon doit être d'au moins {min_size}")

def validate_categorical_data(data: Union[pd.DataFrame, pd.Series], 
                            categories: Optional[List[str]] = None) -> None:
    """
    Valide les données catégorielles.
    
    Args:
        data: Données à valider
        categories: Liste des catégories attendues (optionnel)
        
    Raises:
        TypeError: Si les données ne sont pas catégorielles
        ValueError: Si les catégories ne sont pas valides
    """
    if isinstance(data, pd.DataFrame):
        for col in data.columns:
            if not pd.api.types.is_categorical_dtype(data[col]):
                raise TypeError(f"La colonne {col} doit être catégorielle")
            if categories is not None:
                if not all(cat in data[col].cat.categories for cat in categories):
                    raise ValueError(f"La colonne {col} ne contient pas toutes les catégories requises")
    elif isinstance(data, pd.Series):
        if not pd.api.types.is_categorical_dtype(data):
            raise TypeError("La série doit être catégorielle")
        if categories is not None:
            if not all(cat in data.cat.categories for cat in categories):
                raise ValueError("La série ne contient pas toutes les catégories requises")
    else:
        raise TypeError("Type de données non supporté") 