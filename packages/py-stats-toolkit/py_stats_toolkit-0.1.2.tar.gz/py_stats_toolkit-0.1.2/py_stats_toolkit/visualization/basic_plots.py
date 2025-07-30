from typing import Union, Optional, List, Tuple, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ..utils.data_validation import validate_numeric_data

class BasicPlots:
    """Classe pour créer des graphiques de base."""
    
    def __init__(self, data: Union[np.ndarray, pd.DataFrame, pd.Series],
                 figsize: Tuple[int, int] = (10, 6),
                 style: str = 'seaborn'):
        """
        Initialise le visualiseur.
        
        Args:
            data: Données à visualiser
            figsize: Taille de la figure (largeur, hauteur)
            style: Style de matplotlib à utiliser
        """
        self.data = validate_numeric_data(data)
        self.figsize = figsize
        plt.style.use(style)
    
    def histogram(self, bins: int = 30, density: bool = True,
                 title: str = "Histogramme", xlabel: str = "Valeur",
                 ylabel: str = "Fréquence", **kwargs) -> plt.Figure:
        """
        Crée un histogramme.
        
        Args:
            bins: Nombre de bins
            density: Si True, normalise l'histogramme
            title: Titre du graphique
            xlabel: Label de l'axe x
            ylabel: Label de l'axe y
            **kwargs: Arguments supplémentaires pour plt.hist
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            for column in self.data.columns:
                ax.hist(self.data[column], bins=bins, density=density,
                       label=column, alpha=0.5, **kwargs)
            ax.legend()
        else:
            ax.hist(self.data, bins=bins, density=density, **kwargs)
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        return fig
    
    def boxplot(self, title: str = "Boxplot", ylabel: str = "Valeur",
                **kwargs) -> plt.Figure:
        """
        Crée un boxplot.
        
        Args:
            title: Titre du graphique
            ylabel: Label de l'axe y
            **kwargs: Arguments supplémentaires pour plt.boxplot
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            self.data.boxplot(ax=ax, **kwargs)
        else:
            ax.boxplot(self.data, **kwargs)
        
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        return fig
    
    def scatter(self, x: Optional[Union[np.ndarray, pd.Series]] = None,
                y: Optional[Union[np.ndarray, pd.Series]] = None,
                title: str = "Nuage de points",
                xlabel: str = "X", ylabel: str = "Y",
                **kwargs) -> plt.Figure:
        """
        Crée un nuage de points.
        
        Args:
            x: Données pour l'axe x
            y: Données pour l'axe y
            title: Titre du graphique
            xlabel: Label de l'axe x
            ylabel: Label de l'axe y
            **kwargs: Arguments supplémentaires pour plt.scatter
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            if x is None or y is None:
                raise ValueError("x et y doivent être spécifiés pour un DataFrame")
            ax.scatter(self.data[x], self.data[y], **kwargs)
        else:
            if y is None:
                raise ValueError("y doit être spécifié")
            ax.scatter(x if x is not None else range(len(self.data)),
                      self.data, **kwargs)
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        return fig
    
    def line_plot(self, x: Optional[Union[np.ndarray, pd.Series]] = None,
                  title: str = "Graphique en ligne",
                  xlabel: str = "X", ylabel: str = "Y",
                  **kwargs) -> plt.Figure:
        """
        Crée un graphique en ligne.
        
        Args:
            x: Données pour l'axe x
            title: Titre du graphique
            xlabel: Label de l'axe x
            ylabel: Label de l'axe y
            **kwargs: Arguments supplémentaires pour plt.plot
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            for column in self.data.columns:
                ax.plot(x if x is not None else range(len(self.data)),
                       self.data[column], label=column, **kwargs)
            ax.legend()
        else:
            ax.plot(x if x is not None else range(len(self.data)),
                   self.data, **kwargs)
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        return fig
    
    def bar_plot(self, title: str = "Graphique en barres",
                 xlabel: str = "Catégorie", ylabel: str = "Valeur",
                 **kwargs) -> plt.Figure:
        """
        Crée un graphique en barres.
        
        Args:
            title: Titre du graphique
            xlabel: Label de l'axe x
            ylabel: Label de l'axe y
            **kwargs: Arguments supplémentaires pour plt.bar
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            self.data.plot(kind='bar', ax=ax, **kwargs)
        else:
            ax.bar(range(len(self.data)), self.data, **kwargs)
        
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        return fig 