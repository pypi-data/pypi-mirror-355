"""
Module de métriques statistiques.
Fournit des fonctions pour calculer diverses métriques statistiques.
"""

import numpy as np
import pandas as pd
from typing import Union, List, Optional, Tuple
from scipy import stats

def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcule l'erreur absolue moyenne (MAE).
    
    Args:
        y_true: Valeurs réelles
        y_pred: Valeurs prédites
        
    Returns:
        float: MAE
    """
    return np.mean(np.abs(y_true - y_pred))

def calculate_mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcule l'erreur quadratique moyenne (MSE).
    
    Args:
        y_true: Valeurs réelles
        y_pred: Valeurs prédites
        
    Returns:
        float: MSE
    """
    return np.mean((y_true - y_pred) ** 2)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcule la racine de l'erreur quadratique moyenne (RMSE).
    
    Args:
        y_true: Valeurs réelles
        y_pred: Valeurs prédites
        
    Returns:
        float: RMSE
    """
    return np.sqrt(calculate_mse(y_true, y_pred))

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcule le coefficient de détermination (R²).
    
    Args:
        y_true: Valeurs réelles
        y_pred: Valeurs prédites
        
    Returns:
        float: R²
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def calculate_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calcule l'erreur absolue moyenne en pourcentage (MAPE).
    
    Args:
        y_true: Valeurs réelles
        y_pred: Valeurs prédites
        
    Returns:
        float: MAPE
    """
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def calculate_correlation(x: np.ndarray, y: np.ndarray, method: str = 'pearson') -> float:
    """
    Calcule la corrélation entre deux variables.
    
    Args:
        x: Première variable
        y: Deuxième variable
        method: Méthode de corrélation ('pearson', 'spearman', 'kendall')
        
    Returns:
        float: Coefficient de corrélation
    """
    if method == 'pearson':
        return np.corrcoef(x, y)[0, 1]
    elif method == 'spearman':
        return stats.spearmanr(x, y)[0]
    elif method == 'kendall':
        return stats.kendalltau(x, y)[0]
    else:
        raise ValueError("Méthode non supportée. Utilisez 'pearson', 'spearman' ou 'kendall'.")

def calculate_confidence_interval(data: np.ndarray,
                                confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calcule l'intervalle de confiance pour la moyenne.
    
    Args:
        data: Données
        confidence: Niveau de confiance (0-1)
        
    Returns:
        Tuple[float, float]: Intervalle de confiance (inf, sup)
    """
    mean = np.mean(data)
    std_err = stats.sem(data)
    ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=std_err)
    return ci

def calculate_skewness(data: np.ndarray) -> float:
    """
    Calcule le coefficient d'asymétrie (skewness).
    
    Args:
        data: Données
        
    Returns:
        float: Coefficient d'asymétrie
    """
    return stats.skew(data)

def calculate_kurtosis(data: np.ndarray) -> float:
    """
    Calcule le coefficient d'aplatissement (kurtosis).
    
    Args:
        data: Données
        
    Returns:
        float: Coefficient d'aplatissement
    """
    return stats.kurtosis(data)

def calculate_quantiles(data: np.ndarray,
                       q: List[float] = [0.25, 0.5, 0.75]) -> np.ndarray:
    """
    Calcule les quantiles des données.
    
    Args:
        data: Données
        q: Liste des quantiles à calculer
        
    Returns:
        np.ndarray: Quantiles
    """
    return np.quantile(data, q)

def calculate_statistical_tests(data1: np.ndarray,
                              data2: np.ndarray,
                              test: str = 't-test') -> Tuple[float, float]:
    """
    Effectue des tests statistiques entre deux échantillons.
    
    Args:
        data1: Premier échantillon
        data2: Deuxième échantillon
        test: Type de test ('t-test', 'mann-whitney', 'ks-test')
        
    Returns:
        Tuple[float, float]: Statistique du test et p-valeur
    """
    if test == 't-test':
        return stats.ttest_ind(data1, data2)
    elif test == 'mann-whitney':
        return stats.mannwhitneyu(data1, data2)
    elif test == 'ks-test':
        return stats.ks_2samp(data1, data2)
    else:
        raise ValueError("Test non supporté. Utilisez 't-test', 'mann-whitney' ou 'ks-test'.") 