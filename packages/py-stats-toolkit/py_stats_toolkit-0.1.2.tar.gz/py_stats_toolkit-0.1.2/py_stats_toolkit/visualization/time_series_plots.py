from typing import Union, Optional, List, Tuple, Dict, Any
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.tsa.seasonal import seasonal_decompose
from ..utils.data_validation import validate_numeric_data

class TimeSeriesPlots:
    """Classe pour créer des visualisations de séries temporelles."""
    
    def __init__(self, data: Union[pd.Series, pd.DataFrame],
                 figsize: Tuple[int, int] = (12, 8),
                 style: str = 'seaborn'):
        """
        Initialise le visualiseur de séries temporelles.
        
        Args:
            data: Données temporelles (Series ou DataFrame avec index temporel)
            figsize: Taille de la figure (largeur, hauteur)
            style: Style de matplotlib à utiliser
        """
        if not isinstance(data, (pd.Series, pd.DataFrame)):
            raise TypeError("Les données doivent être une Series ou un DataFrame pandas")
        if not isinstance(data.index, pd.DatetimeIndex):
            raise TypeError("L'index doit être un DatetimeIndex")
        
        self.data = validate_numeric_data(data)
        self.figsize = figsize
        plt.style.use(style)
    
    def time_series_plot(self, title: str = "Série temporelle",
                        **kwargs) -> plt.Figure:
        """
        Crée un graphique de série temporelle.
        
        Args:
            title: Titre du graphique
            **kwargs: Arguments supplémentaires pour plt.plot
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            for column in self.data.columns:
                ax.plot(self.data.index, self.data[column],
                       label=column, **kwargs)
            ax.legend()
        else:
            ax.plot(self.data.index, self.data, **kwargs)
        
        ax.set_title(title)
        ax.set_xlabel("Date")
        ax.set_ylabel("Valeur")
        plt.xticks(rotation=45)
        return fig
    
    def seasonal_decomposition(self, period: int,
                             title: str = "Décomposition saisonnière",
                             **kwargs) -> plt.Figure:
        """
        Crée un graphique de décomposition saisonnière.
        
        Args:
            period: Période de la saisonnalité
            title: Titre du graphique
            **kwargs: Arguments supplémentaires pour seasonal_decompose
            
        Returns:
            Figure matplotlib
        """
        if isinstance(self.data, pd.DataFrame):
            raise TypeError("Les données doivent être une Series pour la décomposition")
        
        decomposition = seasonal_decompose(self.data, period=period, **kwargs)
        
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=self.figsize)
        
        decomposition.observed.plot(ax=ax1)
        ax1.set_title("Observé")
        
        decomposition.trend.plot(ax=ax2)
        ax2.set_title("Tendance")
        
        decomposition.seasonal.plot(ax=ax3)
        ax3.set_title("Saisonnalité")
        
        decomposition.resid.plot(ax=ax4)
        ax4.set_title("Résidus")
        
        fig.suptitle(title)
        plt.tight_layout()
        return fig
    
    def rolling_statistics(self, window: int,
                          title: str = "Statistiques mobiles",
                          **kwargs) -> plt.Figure:
        """
        Crée un graphique des statistiques mobiles.
        
        Args:
            window: Taille de la fenêtre mobile
            title: Titre du graphique
            **kwargs: Arguments supplémentaires pour rolling()
            
        Returns:
            Figure matplotlib
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            for column in self.data.columns:
                rolling_mean = self.data[column].rolling(window=window, **kwargs).mean()
                rolling_std = self.data[column].rolling(window=window, **kwargs).std()
                
                ax.plot(self.data.index, rolling_mean,
                       label=f"{column} (moyenne mobile)")
                ax.fill_between(self.data.index,
                              rolling_mean - 2*rolling_std,
                              rolling_mean + 2*rolling_std,
                              alpha=0.2)
            ax.legend()
        else:
            rolling_mean = self.data.rolling(window=window, **kwargs).mean()
            rolling_std = self.data.rolling(window=window, **kwargs).std()
            
            ax.plot(self.data.index, rolling_mean,
                   label="Moyenne mobile")
            ax.fill_between(self.data.index,
                          rolling_mean - 2*rolling_std,
                          rolling_mean + 2*rolling_std,
                          alpha=0.2)
            ax.legend()
        
        ax.set_title(title)
        ax.set_xlabel("Date")
        ax.set_ylabel("Valeur")
        plt.xticks(rotation=45)
        return fig
    
    def acf_plot(self, lags: int = 40,
                title: str = "Autocorrélation",
                **kwargs) -> plt.Figure:
        """
        Crée un graphique d'autocorrélation.
        
        Args:
            lags: Nombre de décalages à considérer
            title: Titre du graphique
            **kwargs: Arguments supplémentaires pour plot_acf
            
        Returns:
            Figure matplotlib
        """
        from statsmodels.graphics.tsaplots import plot_acf
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            for column in self.data.columns:
                plot_acf(self.data[column], lags=lags, ax=ax,
                        label=column, **kwargs)
            ax.legend()
        else:
            plot_acf(self.data, lags=lags, ax=ax, **kwargs)
        
        ax.set_title(title)
        return fig
    
    def pacf_plot(self, lags: int = 40,
                 title: str = "Autocorrélation partielle",
                 **kwargs) -> plt.Figure:
        """
        Crée un graphique d'autocorrélation partielle.
        
        Args:
            lags: Nombre de décalages à considérer
            title: Titre du graphique
            **kwargs: Arguments supplémentaires pour plot_pacf
            
        Returns:
            Figure matplotlib
        """
        from statsmodels.graphics.tsaplots import plot_pacf
        
        fig, ax = plt.subplots(figsize=self.figsize)
        
        if isinstance(self.data, pd.DataFrame):
            for column in self.data.columns:
                plot_pacf(self.data[column], lags=lags, ax=ax,
                         label=column, **kwargs)
            ax.legend()
        else:
            plot_pacf(self.data, lags=lags, ax=ax, **kwargs)
        
        ax.set_title(title)
        return fig 