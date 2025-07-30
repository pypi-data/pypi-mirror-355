from typing import Union, Optional, List, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler

def standardize_data(data: Union[np.ndarray, pd.DataFrame, pd.Series],
                    scaler: Optional[StandardScaler] = None) -> Tuple[Union[np.ndarray, pd.DataFrame, pd.Series], StandardScaler]:
    """
    Standardise les données (moyenne = 0, écart-type = 1).
    
    Args:
        data: Données à standardiser
        scaler: Scaler pré-entraîné (optionnel)
        
    Returns:
        Tuple[Données standardisées, Scaler]
    """
    if scaler is None:
        scaler = StandardScaler()
        
    if isinstance(data, pd.DataFrame):
        scaled_data = pd.DataFrame(
            scaler.fit_transform(data) if scaler is None else scaler.transform(data),
            columns=data.columns,
            index=data.index
        )
    elif isinstance(data, pd.Series):
        scaled_data = pd.Series(
            scaler.fit_transform(data.values.reshape(-1, 1)).ravel() if scaler is None else scaler.transform(data.values.reshape(-1, 1)).ravel(),
            index=data.index,
            name=data.name
        )
    else:  # numpy array
        scaled_data = scaler.fit_transform(data) if scaler is None else scaler.transform(data)
    
    return scaled_data, scaler

def normalize_data(data: Union[np.ndarray, pd.DataFrame, pd.Series],
                  scaler: Optional[MinMaxScaler] = None,
                  feature_range: Tuple[float, float] = (0, 1)) -> Tuple[Union[np.ndarray, pd.DataFrame, pd.Series], MinMaxScaler]:
    """
    Normalise les données dans un intervalle spécifié.
    
    Args:
        data: Données à normaliser
        scaler: Scaler pré-entraîné (optionnel)
        feature_range: Intervalle de normalisation
        
    Returns:
        Tuple[Données normalisées, Scaler]
    """
    if scaler is None:
        scaler = MinMaxScaler(feature_range=feature_range)
        
    if isinstance(data, pd.DataFrame):
        normalized_data = pd.DataFrame(
            scaler.fit_transform(data) if scaler is None else scaler.transform(data),
            columns=data.columns,
            index=data.index
        )
    elif isinstance(data, pd.Series):
        normalized_data = pd.Series(
            scaler.fit_transform(data.values.reshape(-1, 1)).ravel() if scaler is None else scaler.transform(data.values.reshape(-1, 1)).ravel(),
            index=data.index,
            name=data.name
        )
    else:  # numpy array
        normalized_data = scaler.fit_transform(data) if scaler is None else scaler.transform(data)
    
    return normalized_data, scaler

def robust_scale_data(data: Union[np.ndarray, pd.DataFrame, pd.Series],
                     scaler: Optional[RobustScaler] = None) -> Tuple[Union[np.ndarray, pd.DataFrame, pd.Series], RobustScaler]:
    """
    Applique une normalisation robuste aux données.
    
    Args:
        data: Données à normaliser
        scaler: Scaler pré-entraîné (optionnel)
        
    Returns:
        Tuple[Données normalisées, Scaler]
    """
    if scaler is None:
        scaler = RobustScaler()
        
    if isinstance(data, pd.DataFrame):
        scaled_data = pd.DataFrame(
            scaler.fit_transform(data) if scaler is None else scaler.transform(data),
            columns=data.columns,
            index=data.index
        )
    elif isinstance(data, pd.Series):
        scaled_data = pd.Series(
            scaler.fit_transform(data.values.reshape(-1, 1)).ravel() if scaler is None else scaler.transform(data.values.reshape(-1, 1)).ravel(),
            index=data.index,
            name=data.name
        )
    else:  # numpy array
        scaled_data = scaler.fit_transform(data) if scaler is None else scaler.transform(data)
    
    return scaled_data, scaler

def handle_missing_values(data: Union[np.ndarray, pd.DataFrame, pd.Series],
                         strategy: str = 'mean',
                         fill_value: Optional[float] = None) -> Union[np.ndarray, pd.DataFrame, pd.Series]:
    """
    Gère les valeurs manquantes selon différentes stratégies.
    
    Args:
        data: Données à traiter
        strategy: Stratégie de remplacement ('mean', 'median', 'mode', 'constant')
        fill_value: Valeur de remplacement pour la stratégie 'constant'
        
    Returns:
        Données avec valeurs manquantes traitées
    """
    if isinstance(data, pd.DataFrame):
        if strategy == 'mean':
            return data.fillna(data.mean())
        elif strategy == 'median':
            return data.fillna(data.median())
        elif strategy == 'mode':
            return data.fillna(data.mode().iloc[0])
        elif strategy == 'constant':
            if fill_value is None:
                raise ValueError("fill_value doit être spécifié pour la stratégie 'constant'")
            return data.fillna(fill_value)
        else:
            raise ValueError("Stratégie non supportée")
            
    elif isinstance(data, pd.Series):
        if strategy == 'mean':
            return data.fillna(data.mean())
        elif strategy == 'median':
            return data.fillna(data.median())
        elif strategy == 'mode':
            return data.fillna(data.mode().iloc[0])
        elif strategy == 'constant':
            if fill_value is None:
                raise ValueError("fill_value doit être spécifié pour la stratégie 'constant'")
            return data.fillna(fill_value)
        else:
            raise ValueError("Stratégie non supportée")
            
    else:  # numpy array
        if strategy == 'mean':
            return np.nan_to_num(data, nan=np.nanmean(data))
        elif strategy == 'median':
            return np.nan_to_num(data, nan=np.nanmedian(data))
        elif strategy == 'constant':
            if fill_value is None:
                raise ValueError("fill_value doit être spécifié pour la stratégie 'constant'")
            return np.nan_to_num(data, nan=fill_value)
        else:
            raise ValueError("Stratégie non supportée") 