import os
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from matplotlib.colors import LogNorm
from pulp import LpContinuous, LpMinimize, LpProblem, LpVariable, lpSum

# Afficher toutes les colonnes
pd.set_option("display.max_columns", None)

# Afficher toutes les lignes
pd.set_option("display.max_rows", None)

pd.set_option("future.no_silent_downcasting", True)

import grafs_e.graphes_objet as gr
from grafs_e.donnees import *


class DataLoader:
    """Load the GRAFS Excel file (written by Julia Le Noë).

    This class makes it possible to access all the data stored in the Excel file.
    Currently, only yearly data (area, production, etc.) are accessed.
    Stable data is stored in the 'GRAFS_data.xlsx' file.

    This class will become obsolete once a proper database is built.

    No arguments are required; the script automatically finds the Excel sheet.
    Loading time: approximately 40 seconds.
    """

    def __init__(self):  # , year, region):
        file_path = os.path.dirname(__file__)
        self.sheets_dict = pd.read_excel(os.path.join(file_path, "data/full_grafs.xlsx"), sheet_name=None)
        self.data_path = os.path.join(file_path, "data")

    def pre_process_df(self, year, region):
        """Select the data sheet for a specific year and region.

        Args:
            year (str): The year for which to select the data.
            region (str): The region for which to select the data. Not used (deprecated). To access ta data of a specific region, use df[["nom", region]]
        """
        df = self.sheets_dict["pvar" + year].copy()
        df.loc[df.index[0], "Primary data, parameters, pre-treatments "] = "nom"
        df.columns = df.iloc[0]
        df["index_excel"] = df.index + 2
        return df

    def get_import_feed(self, year, region):
        """Select in the GRAFS excel the nitrogen import feed.
        Args:
            year (str): The year for which to select the data.
            region (str): The region for which to select the data.
        """
        df = self.sheets_dict["GRAFS" + year].copy()
        df.columns = df.iloc[0]
        correct_region = {
            "Pyrénées occid": "Pyrénées occidentales",
            "Pyrénées Orient": "Pyrénées Orientales",
        }
        if region in correct_region.keys():
            region = correct_region[region]
        return df[region].iloc[32]


class CultureData:
    """This class processes and creates a dataframe with crop data for a specific year and region.

    The class uses the provided DataLoader instance to load and preprocess the data. It extracts relevant crop-related
    information such as surface area, crop production, nitrogen production, and fertilization needs, and combines them into
    a comprehensive dataframe.

    Args:
        data_loader (DataLoader): An instance of the DataLoader class used to load and preprocess the data.
        region (str): The region for which to create the crop dataframe.
        year (str): The year for which to create the crop dataframe.
        categories_mapping (dict): A dictionary used to classify each crop, mapping crop names to categories.

    Attributes:
        region (str): The region for which the crop data is processed.
        year (str): The year for which the crop data is processed.
        df (pandas.DataFrame): A dataframe containing the preprocessed data for the specified year and region.
        data_path (str): The path to the directory containing the data files.
        categories_mapping (dict): A dictionary mapping crop names to their respective categories.
        df_cultures (pandas.DataFrame): The final dataframe containing the processed crop data, including surface area,
                                        crop production, nitrogen production, yield, and fertilization needs.

    Methods:
        create_culture_dataframe():
            Processes the raw data to create the crop dataframe. This dataframe includes:
            - Crop surface area (in hectares).
            - Crop production (in kton DFW).
            - Nitrogen production (in kton N).
            - Yield per hectare (in qtl/ha).
            - Fertilization needs per hectare (in kgN/ha).
            The method performs various data transformations and calculations, including filling missing values with zero.
    """

    def __init__(self, data_loader, year, region, categories_mapping=categories_mapping):
        """Initializes the CultureData class by preprocessing the data for the given year, region, and categories.

        Args:
            data_loader (DataLoader): An instance of the DataLoader class used to load and preprocess the data.
            year (str): The year for which to create the crop dataframe.
            region (str): The region for which to create the crop dataframe.
            categories_mapping (dict): A dictionary used to classify each crop, mapping crop names to categories.
        """
        self.region = region
        self.year = year
        self.df = data_loader.pre_process_df(self.year, self.region)
        self.data_path = data_loader.data_path
        self.categories_mapping = categories_mapping
        self.df_cultures = self.create_culture_dataframe()

    def create_culture_dataframe(self):
        """Processes the raw data to create the crop dataframe.

        The dataframe includes:
        - Crop surface area (in hectares).
        - Crop production (in kton DFW).
        - Nitrogen production (in kton N).
        - Yield per hectare (in qtl/ha).
        - Fertilization needs per hectare (in kgN/ha).

        This method performs the following steps:
        - Extracts crop surface and production data from the main dataframe.
        - Reads additional crop-specific data (fertilization and nitrogen content) from an external Excel file.
        - Calculates the nitrogen production and yield based on crop production and surface area.
        - Computes fertilization needs per hectare based on crop yield.
        - Fills missing values with zero.

        Returns:
            pandas.DataFrame: A dataframe containing the processed crop data.
        """
        df = self.df
        region = self.region
        data_path = self.data_path

        # Extraire les données de surface
        surface_data = df[(df["index_excel"] >= 259) & (df["index_excel"] <= 294)][["nom", region]]
        surface_dict = surface_data.set_index("nom")[region].to_dict()
        surface_dict["Rice"] = surface_dict.pop("rice")
        surface_dict["Forage cabbages"] = surface_dict.pop("Forage cabbages & roots")

        # Extraire les données de production végétale
        vege_prod_data = df[(df["index_excel"] >= 183) & (df["index_excel"] <= 218)][["nom", region]]
        vege_prod_dict = vege_prod_data.set_index("nom")[region].to_dict()

        # Extraire les taux de surface avec épendage
        epend = pd.read_excel(
            os.path.join(data_path, "GRAFS_data.xlsx"),
            sheet_name="crops",
        )

        epend = epend.drop("Note", axis=1)
        epend = epend.set_index("Culture")
        epend["Area (ha)"] = pd.DataFrame.from_dict(surface_dict, orient="index", columns=["Area (ha)"])
        epend["Crop Production (ktonDFW)"] = pd.DataFrame.from_dict(
            vege_prod_dict, orient="index", columns=["Crop Production (ktonDFW)"]
        )
        # Calcul de l'azote disponible pour les cultures
        epend["Nitrogen Production (ktN)"] = epend["Crop Production (ktonDFW)"] * epend["Nitrogen Content (%)"] / 100
        mask = epend["Area (ha)"] != 0

        epend.loc[mask, "Yield (qtl/ha)"] = (
            epend.loc[mask, "Crop Production (ktonDFW)"] * 1e4 / epend.loc[mask, "Area (ha)"]
        )

        epend.loc[mask, "Yield (kgN/ha)"] = (
            epend.loc[mask, "Nitrogen Production (ktN)"] / epend.loc[mask, "Area (ha)"] * 1e6
        )

        mask = epend["Fertilization Need (kgN/qtl)"] > 0
        epend["Surface Fertilization Need (kgN/ha)"] = epend["Surface Fertilization Need (kgN/ha)"].astype(
            "float64", copy=False
        )
        epend.loc[mask, "Surface Fertilization Need (kgN/ha)"] = (
            epend.loc[mask, "Fertilization Need (kgN/qtl)"] * epend.loc[mask, "Yield (qtl/ha)"]
        )

        epend = epend.fillna(0)

        return epend


class ElevageData:
    """This class processes and creates a dataframe containing livestock data for a specific year and region.

    The class uses data from the provided DataLoader instance, filters and processes it to generate
    a dataframe containing livestock production and emissions data.

    Args:
        data_loader (DataLoader): An instance of the DataLoader class used to load and preprocess the data.
        year (str): The year for which to generate the livestock dataframe.
        region (str): The region for which to generate the livestock dataframe.

    Attributes:
        region (str): The region for which the livestock data is processed.
        year (str): The year for which the livestock data is processed.
        df (pandas.DataFrame): A dataframe containing the preprocessed data for the specified year and region.
        data_path (str): The path to the directory containing the data files.
        dataloader (DataLoader): The instance of the DataLoader used to load the data.
        df_elevage (pandas.DataFrame): The final dataframe containing livestock production and emissions data.

    Methods:
        create_elevage_dataframe():
            Processes the pre-loaded data to create the livestock dataframe, which includes both production data
            and associated emission data. The production data is filtered and matched with gas emission data
            for the specified region, and missing values are filled with zero.
    """

    def __init__(self, data_loader, year, region):
        """Initializes the ElevageData class by preprocessing the data for the given year and region.

        Args:
            data_loader (DataLoader): An instance of the DataLoader class used to load and preprocess the data.
            year (str): The year for which to generate the livestock dataframe.
            region (str): The region for which to generate the livestock dataframe.
        """
        self.region = region
        self.year = year
        self.df = data_loader.pre_process_df(self.year, self.region)
        self.data_path = data_loader.data_path
        self.dataloader = data_loader
        self.df_elevage = self.create_elevage_dataframe()

    def create_elevage_dataframe(self):
        """Processes the raw data to create the livestock dataframe.

        The dataframe includes the following:
        - Livestock production data (in kton carcass) for the specified region.
        - Gas emissions data related to livestock (volatilisation) linked by the 'Elevage' index.

        Returns:
            pandas.DataFrame: A dataframe containing the processed livestock production data and gas emissions data.
        """
        df = self.df
        region = self.region
        data_path = self.data_path

        # Production animale, attention, contrairement au reste, ici on est en kton carcasse
        production_data = df[(df["index_excel"] >= 1017) & (df["index_excel"] <= 1022)][["nom", region]]
        production_dict = production_data.set_index("nom")[region].to_dict()

        gas_em = pd.read_excel(os.path.join(data_path, "GRAFS_data.xlsx"), sheet_name="Volatilisation").set_index(
            "Elevage"
        )

        # Construction du dictionnaire combined_data
        combined_data = {
            "Production": production_dict,
        }

        combined_df = pd.DataFrame(combined_data)

        combined_df = combined_df.join(gas_em, how="left")

        combined_df = combined_df.fillna(0)
        return combined_df


class FluxGenerator:
    """This class generates and manages the transition matrix of fluxes between various sectors (e.g., agriculture, livestock, industry, trade).

    The transition matrix is used to model the flow of resources or interactions between sectors, where each entry in the matrix represents the relationship or flow between a source sector and a target sector.

    Args:
        labels (list): A list of labels representing the sectors (e.g., ['agriculture', 'livestock', 'industry', 'trade']) in the model. These labels are used to index the transition matrix and identify the sectors in the flux calculations.

    Attributes:
        labels (list): The list of labels (sectors) that are used to define the transition matrix.
        label_to_index (dict): A dictionary mapping each label (sector) to its corresponding index in the adjacency matrix.
        n (int): The number of sectors (i.e., the length of the labels list).
        adjacency_matrix (numpy.ndarray): A square matrix of size n x n representing the fluxes between sectors. Each element in the matrix holds the transition coefficient between a source and a target sector.

    Methods:
        generate_flux(source, target):
            Generates and updates the transition matrix by calculating flux coefficients between the source and target sectors. The coefficients are based on the provided `source` and `target` dictionaries.

        get_coef(source_label, target_label):
            Retrieves the transition coefficient for the flux between two sectors (identified by their labels) from the transition matrix.
    """

    def __init__(self, labels):
        """Initializes the FluxGenerator with a list of sector labels.

        Args:
            labels (list): List of labels representing sectors in the model.
        """
        self.labels = labels
        self.label_to_index = {label: index for index, label in enumerate(self.labels)}
        self.n = len(self.labels)
        self.adjacency_matrix = np.zeros((self.n, self.n))

    def generate_flux(self, source, target):
        """Generates and updates the transition matrix by calculating the flux coefficients between the source and target sectors.

        Args:
            source (dict): A dictionary representing the source sector, where keys are sector labels and values are the corresponding flux values.
            target (dict): A dictionary representing the target sector, where keys are sector labels and values are the corresponding flux values.

        This method updates the adjacency matrix by computing the flux between all pairs of source and target sectors.
        A flux coefficient is calculated as the product of the corresponding values from the `source` and `target` dictionaries.
        If the coefficient exceeds a small threshold (10^-7), it is added to the matrix at the corresponding position.
        """
        for source_label, source_value in source.items():
            source_index = self.label_to_index.get(source_label)
            if source_index is None:
                continue
            for target_label, target_value in target.items():
                coefficient = source_value * target_value
                target_index = self.label_to_index.get(target_label)
                if target_index is not None:
                    if coefficient > 10**-7:
                        self.adjacency_matrix[source_index, target_index] += coefficient
                else:
                    print(f"{target_label} not found in label_to_index")

    def get_coef(self, source_label, target_label):
        """Retrieves the transition coefficient between two sectors from the adjacency matrix.

        Args:
            source_label (str): The label of the source sector.
            target_label (str): The label of the target sector.

        Returns:
            float or None: The transition coefficient between the source and target sectors. Returns None if either sector is not found in the matrix.
        """
        source_index = self.label_to_index.get(source_label)
        target_index = self.label_to_index.get(target_label)
        if source_index is not None and target_index is not None:
            return self.adjacency_matrix[source_index][target_index]
        else:
            return None


class NitrogenFlowModel:
    """This class models the nitrogen flow in an agricultural system, calculating fluxes and nitrogen dynamics
    for different sectors (e.g., crops, livestock) over a given year and region.

    The model incorporates various processes, including crop production, animal production, nitrogen emissions,
    and fertilization, and computes the corresponding nitrogen fluxes between sectors using transition matrices.

    This class provides methods to compute fluxes, generate heatmaps, and access matrices such as the transition matrix,
    core matrix, and adjacency matrix.

    For a detailed explanation of the model's methodology and mathematical foundations, please refer to the associated
    scientific paper: Tracking Nitrogen Dynamics: A Disaggregated Approach for French Agro-Food Systems, 2025, Adrien Fauste-Gay (pre-print).

    Args:
        data (DataLoader): An instance of the DataLoader class to load and preprocess the data.
        year (str): The year for which to compute the nitrogen flow model.
        region (str): The region for which to compute the nitrogen flow model.
        categories_mapping (dict, optional): A dictionary used to classify each crop. Defaults to categories_mapping.
        labels (list, optional): A list of labels representing the sectors in the model. Defaults to labels.
        cultures (CultureData, optional): An instance of the CultureData class for crop data processing.
        legumineuses (list, optional): A list representing leguminous crops in the model.
        prairies (list, optional): A list representing grasslands and prairies in the model.
        betail (list, optional): A list representing livestock categories in the model.
        Pop (list, optional): A list representing the population data.
        ext (list, optional): A list representing external data or processes affecting nitrogen fluxes.

    Attributes:
        year (str): The year for which the nitrogen flow model is computed.
        region (str): The region for which the nitrogen flow model is computed.
        categories_mapping (dict): The dictionary used to classify crops.
        labels (list): The list of labels representing the sectors in the model.
        data_loader (DataLoader): The instance of the DataLoader used to load the data.
        culture_data (CultureData): An instance of the CultureData class for crop data.
        elevage_data (ElevageData): An instance of the ElevageData class for livestock data.
        flux_generator (FluxGenerator): An instance of the FluxGenerator class to generate flux coefficients.
        df_cultures (pandas.DataFrame): The dataframe containing crop data.
        df_elevage (pandas.DataFrame): The dataframe containing livestock data.
        adjacency_matrix (numpy.ndarray): The matrix representing nitrogen fluxes between sectors.
        label_to_index (dict): A dictionary mapping sector labels to matrix indices.

    Methods:
        compute_fluxes():
            Computes the nitrogen fluxes between the sectors of the model. This method populates the adjacency matrix
            with flux coefficients based on the interactions between crops, livestock, emissions, and fertilization.

        plot_heatmap():
            Generates a heatmap visualization of the transition matrix for nitrogen fluxes.

        plot_heatmap_interactive():
            Generates an interactive heatmap for the nitrogen fluxes.

        get_df_culture():
            Returns the dataframe containing crop data.

        get_df_elevage():
            Returns the dataframe containing livestock data.

        get_transition_matrix():
            Returns the transition matrix representing nitrogen fluxes between sectors.

        get_core_matrix():
            Returns the core matrix representing the primary fluxes in the system.

        get_adjacency_matrix():
            Returns the adjacency matrix, which is used to represent the complete set of nitrogen fluxes between sectors.

        extract_input_output_matrixs():
            Extracts and returns the input-output matrices of nitrogen fluxes.

        imported_nitrogen():
            Returns the total amount of imported nitrogen in the system.

        net_imported_plant():
            Returns the net imported nitrogen for plants.

        net_imported_animal():
            Returns the net imported nitrogen for livestock.

        total_plant_production():
            Returns the total plant production in the model.

        stacked_plant_production():
            Returns a stacked representation of plant production data.
    """

    def __init__(
        self,
        data,
        year,
        region,
        categories_mapping=categories_mapping,
        labels=labels,
        cultures=cultures,
        legumineuses=legumineuses,
        prairies=prairies,
        betail=betail,
        Pop=Pop,
        ext=ext,
    ):
        """Initializes the NitrogenFlowModel class with the necessary data and model parameters.

        Args:
            data (DataLoader): An instance of the DataLoader class to load and preprocess the data.
            year (str): The year for which to compute the nitrogen flow model.
            region (str): The region for which to compute the nitrogen flow model.
            categories_mapping (dict, optional): A dictionary used to classify each crop. Defaults to categories_mapping.
            labels (list, optional): A list of labels representing the sectors in the model. Defaults to labels.
            cultures (CultureData, optional): An instance of the CultureData class for crop data processing.
            legumineuses (list, optional): A list representing leguminous crops in the model.
            prairies (list, optional): A list representing grasslands and prairies in the model.
            betail (list, optional): A list representing livestock categories in the model.
            Pop (list, optional): A list representing the population data.
            ext (list, optional): A list representing external data or processes affecting nitrogen fluxes.
        """
        self.year = year
        self.region = region
        self.categories_mapping = categories_mapping
        self.labels = labels
        self.cultures = cultures
        self.legumineuses = legumineuses
        self.prairies = prairies
        self.betail = betail
        self.Pop = Pop
        self.ext = ext

        self.data_loader = data  # DataLoader(year, region)
        self.culture_data = CultureData(self.data_loader, self.year, self.region, categories_mapping)
        self.elevage_data = ElevageData(self.data_loader, self.year, self.region)
        self.flux_generator = FluxGenerator(labels)

        self.df_cultures = self.culture_data.df_cultures
        self.df_elevage = self.elevage_data.df_elevage
        self.adjacency_matrix = self.flux_generator.adjacency_matrix
        self.label_to_index = self.flux_generator.label_to_index

        self.compute_fluxes()

    def plot_heatmap(self):
        """
        Generates a static heatmap to visualize the nitrogen flux transition matrix.

        The heatmap displays the nitrogen fluxes between sectors using a logarithmic color scale. It provides a visual representation
        of the relative magnitudes of nitrogen fluxes, where each cell in the matrix corresponds to a transition from one sector
        (source) to another (target).

        Features of the heatmap:
        - **Logarithmic scale** for better visualization of fluxes with wide value ranges (`LogNorm` is used with `vmin=10^-4` and `vmax` set to the maximum value in the adjacency matrix).
        - **Color palette** is reversed "plasma" (`plasma_r`), with the color bar indicating flux magnitudes in kton/year.
        - **Grid**: A light gray grid is added for visual separation of cells.
        - **Labels**: Axis labels are moved to the top of the heatmap, with tick labels rotated for better readability.
        - **Legend**: Each sector is labeled with its corresponding index (e.g., "1: Agriculture"), positioned next to the heatmap.

        Args:
            None

        Returns:
            None: Displays the heatmap plot on screen.

        Note:
            This method uses `matplotlib` and `seaborn` for visualization. Make sure these libraries are installed.
        """
        plt.figure(figsize=(10, 12), dpi=500)
        ax = plt.gca()

        # Créer la heatmap sans grille pour le moment
        norm = LogNorm(vmin=10**-4, vmax=self.adjacency_matrix.max())
        sns.heatmap(
            self.adjacency_matrix,
            xticklabels=range(1, len(self.labels) + 1),
            yticklabels=range(1, len(self.labels) + 1),
            cmap="plasma_r",
            annot=False,
            norm=norm,
            ax=ax,
            cbar_kws={"label": "ktN/year", "orientation": "horizontal", "pad": 0.02},
        )

        # Ajouter la grille en gris clair
        ax.grid(True, color="lightgray", linestyle="-", linewidth=0.5)

        # Déplacer les labels de l'axe x en haut
        ax.xaxis.set_ticks_position("top")  # Placer les ticks en haut
        ax.xaxis.set_label_position("top")  # Placer le label en haut

        # Rotation des labels de l'axe x
        plt.xticks(rotation=90, fontsize=8)
        plt.yticks(rotation=0, fontsize=8)
        # Assurer que les axes sont égaux
        ax.set_aspect("equal", adjustable="box")
        # Ajouter des labels et un titre
        plt.xlabel("Target", fontsize=14, fontweight="bold")
        plt.ylabel("Source", fontsize=14, fontweight="bold")
        # plt.title(f'Heatmap of adjacency matrix for {region} in {year}')

        legend_labels = [f"{i + 1}: {label}" for i, label in enumerate(self.labels)]
        for i, label in enumerate(legend_labels):
            ax.text(
                1.05,
                1 - 1.1 * (i + 0.5) / len(legend_labels),
                label,
                transform=ax.transAxes,
                fontsize=10,
                va="center",
                ha="left",
                color="black",
                verticalalignment="center",
                horizontalalignment="left",
                linespacing=20,
            )  # Augmenter l'espacement entre les lignes

        # plt.subplots_adjust(bottom=0.2, right=0.85)  # Réduire l'espace vertical entre la heatmap et la colorbar
        # Afficher la heatmap
        plt.show()

    def plot_heatmap_interactive(self):
        """
        Generates an interactive heatmap using Plotly to visualize the nitrogen flux transition matrix.

        The heatmap has the following features:
        - Logarithmic scale (simulated via log10(z)) to handle wide-ranging values.
        - A horizontal colorbar placed at the bottom of the plot.
        - A legend that maps matrix indices to sector labels, positioned on the right, ensuring no overlap.
        - The X-axis is displayed at the top of the plot, and the title is centered above the plot.

        This visualization helps to understand the relative magnitudes of the nitrogen fluxes between sectors
        in a clear and interactive manner.

        Returns:
            plotly.graph_objects.Figure: An interactive Plotly figure containing the heatmap.
        """

        # 1) Préparation des labels numériques
        x_labels = list(range(1, len(self.labels) + 1))
        y_labels = list(range(1, len(self.labels) + 1))

        # Si vous ignorez la dernière ligne/colonne comme dans votre code :
        # adjacency_subset = self.adjacency_matrix[: len(self.labels), : len(self.labels)]

        adj = np.array(self.adjacency_matrix)  # ou .copy()
        adjacency_subset = adj[: len(self.labels), : len(self.labels)].copy()

        # 2) Gestion min/max et transformation log10
        cmin = max(1e-4, np.min(adjacency_subset[adjacency_subset > 0]))
        cmax = 100  # np.max(adjacency_subset)
        log_matrix = np.where(adjacency_subset > 0, np.log10(adjacency_subset), np.nan)

        # 3) Construire un tableau 2D de chaînes pour le survol
        #    Même dimension que log_matrix
        strings_matrix = []
        for row_i, y_val in enumerate(y_labels):
            row_texts = []
            for col_i, x_val in enumerate(x_labels):
                # Valeur réelle (non log) => adjacency_subset[row_i, col_i]
                real_val = adjacency_subset[row_i, col_i]
                if np.isnan(real_val):
                    real_val_str = "0"
                else:
                    real_val_str = f"{real_val:.2e}"  # format décimal / exposant
                # Construire la chaîne pour la tooltip
                # y_val et x_val sont les indices 1..N
                # self.labels[y_val] = nom de la source, self.labels[x_val] = nom de la cible
                tooltip_str = f"Source : {self.labels[y_val - 1]}<br>Target : {self.labels[x_val - 1]}<br>Value  : {real_val_str} ktN/yr"
                row_texts.append(tooltip_str)
            strings_matrix.append(row_texts)

        # 3) Tracé Heatmap avec go.Figure + go.Heatmap
        #    On règle "zmin" et "zmax" en valeurs log10
        #    pour contrôler la gamme de couleurs
        trace = go.Heatmap(
            z=log_matrix,
            x=x_labels,
            y=y_labels,
            colorscale="Plasma_r",
            zmin=np.log10(cmin),
            zmax=np.log10(cmax),
            text=strings_matrix,  # tableau 2D de chaînes
            hoverinfo="text",  # on n'affiche plus x, y, z bruts
            # Colorbar horizontale
            colorbar=dict(
                title="ktN/year",
                orientation="h",
                x=0.5,  # centré horizontalement
                xanchor="center",
                y=-0.15,  # en dessous de la figure
                thickness=15,  # épaisseur
                len=1,  # longueur en fraction de la largeur
            ),
            # Valeurs de survol -> vous verrez log10(...) par défaut
            # Pour afficher la valeur réelle, on peut plus tard utiliser "customdata"
        )

        # Créer la figure et y ajouter le trace
        fig = go.Figure(data=[trace])

        # 4) Discrétisation manuelle des ticks sur la colorbar
        #    On veut afficher l'échelle réelle (et pas log10)
        #    => calcul de tickvals en log10, et ticktext en 10^(tickvals)
        tickvals = np.linspace(np.floor(np.log10(cmin)), np.ceil(np.log10(cmax)), num=7)
        ticktext = [10**x for x in range(-4, 3, 1)]  # [f"{10**v:.2e}" for v in tickvals]
        # Mettre à jour le trace pour forcer l'affichage
        fig.data[0].update(
            colorbar=dict(
                title="ktN/year",
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.15,
                thickness=25,
                len=1,
                tickmode="array",
                tickvals=tickvals,
                ticktext=ticktext,
            )
        )

        # 5) Configuration de la mise en page
        fig.update_layout(
            width=1000,
            height=1000,
            margin=dict(t=0, b=0, l=0, r=220),  # espace à droite pour la légende
        )
        fig.update_layout(yaxis_scaleanchor="x")

        # Axe X en haut
        fig.update_xaxes(
            title="Target",
            side="top",  # place les ticks en haut
            tickangle=90,  # rotation
            tickmode="array",
            tickfont=dict(size=10),
            tickvals=x_labels,  # forcer l'affichage 1..N
            ticktext=[str(x) for x in x_labels],
        )

        # Axe Y : inverser l'ordre pour un style "matriciel" standard
        fig.update_yaxes(
            title="Source",
            autorange="reversed",
            tickmode="array",
            tickfont=dict(size=10),
            tickvals=y_labels,
            ticktext=[str(y) for y in y_labels],
        )

        # 6) Ajouter la légende à droite
        #    Format : "1: label[0]" ... vertical
        legend_text = "<br>".join(f"{i + 1} : {lbl}" for i, lbl in enumerate(self.labels))
        fig.add_annotation(
            x=1.25,  # un peu à droite
            y=0.45,  # centré en hauteur
            xref="paper",
            yref="paper",
            showarrow=False,
            text=legend_text,
            align="left",
            valign="middle",
            font=dict(size=11),
            bordercolor="rgba(0,0,0,0)",
            borderwidth=1,
            borderpad=4,
            bgcolor="rgba(0,0,0,0)",
        )

        return fig

    def compute_fluxes(self):
        """Computes the nitrogen fluxes for all sectors in the model.

        This method populates the adjacency matrix with flux coefficients based on sector interactions. These interactions
        include crop production, livestock production, nitrogen emissions, and fertilization. The coefficients are used to
        model the flow of nitrogen between sectors over the specified year and region.

        The computation involves complex mathematical processes, which are detailed in the associated scientific methodology
        paper: Tracking Nitrogen Dynamics: A Disaggregated Approach for French Agro-Food Systems, 2025, Adrien Fauste-Gay (pre-print).

        For an in-depth explanation of the model's functioning, please refer to the accompanying paper.
        """
        # Extraire les variables nécessaires
        df_cultures = self.df_cultures
        df_elevage = self.df_elevage
        adjacency_matrix = self.adjacency_matrix
        label_to_index = self.label_to_index
        year = self.year
        region = self.region
        data_loader = self.data_loader
        flux_generator = self.flux_generator
        data = data_loader.pre_process_df(year, region)

        # Gestion du cas particulier pour 'Straw'
        cereales = ["Wheat", "Rye", "Barley", "Oat", "Grain maize", "Other cereals"]
        somme_azote_produit_cereales = df_cultures["Nitrogen Production (ktN)"][cereales].sum()
        somme_surface_cereales = df_cultures["Area (ha)"][cereales].sum()
        df_cultures.loc["Straw", "Area (ha)"] = int(
            somme_surface_cereales
            * df_cultures.loc["Straw", "Nitrogen Production (ktN)"]
            / somme_azote_produit_cereales
        )
        for cereal in cereales:
            df_cultures.loc[cereal, "Area (ha)"] -= int(
                df_cultures.loc["Straw", "Area (ha)"] * df_cultures.loc[cereal, "Area (ha)"] / somme_surface_cereales
            )
        df_cultures.loc["Straw", "Yield (qtl/ha)"] = (
            df_cultures["Crop Production (ktonDFW)"]["Straw"] / df_cultures["Area (ha)"]["Straw"] * 1000
        )

        ## Flux depuis 'other sectors' (seeds) vers les cibles sélectionnées
        # selected_data = data[(data["index_excel"] >= 106) & (data["index_excel"] <= 139)]
        # target = selected_data.set_index("nom")[region].to_dict()
        # source = {"other sectors": 1}
        # flux_generator.generate_flux(source, target)

        target = (df_cultures["Seed input (kt seeds/kt Ymax)"] * df_cultures["Nitrogen Production (ktN)"]).to_dict()
        source = {"other sectors": 1}
        flux_generator.generate_flux(source, target)

        ## Dépôt atmosphérique
        coef_surf = data[data["index_excel"] == 41][region].item()
        source = {"N2O emission": 0.1, "NH3 volatilization": 0.9}
        target = (
            coef_surf * df_cultures["Area (ha)"] / df_cultures["Area (ha)"].sum()
        ).to_dict()  # Dépôt proportionnel aux surface
        flux_generator.generate_flux(source, target)

        ## Fixation symbiotique
        target_fixation = (
            df_cultures["N fixation coef (kgN/kgN)"] * df_cultures["Nitrogen Production (ktN)"]
        ).to_dict()
        source_fixation = {"atmospheric N2": 1}
        flux_generator.generate_flux(source_fixation, target_fixation)
        df_cultures["Symbiotic fixation (ktN)"] = df_cultures.index.map(target_fixation).fillna(0)

        ## Épandage de boue sur les champs
        # Fonction pour calculer la redistribution de boues autour de Paris
        def compute_N_supp():
            if self.region not in ["Eure", "Ile de France", "Eure-et-Loir", "Picardie"]:
                return 0, 0
            if self.region == "Ile de France":
                factor = -0.5
            elif self.region in ["Eure", "Eure-et-Loir"]:
                factor = 0.15
            elif self.region == "Picardie":
                factor = 0.2
            data_IDF = self.data_loader.pre_process_df(year, "Ile de France")
            pop_IDF = data_IDF[data_IDF["index_excel"] == 5]["Ile de France"].item()
            prop_urb_IDF = data_IDF[data_IDF["nom"] == "Urban population"]["Ile de France"].item() / 100
            N_cons_cap_IDF = data_IDF[data_IDF["index_excel"] == 8]["Ile de France"].item()
            N_prop_recy_urb_IDF = (
                data_IDF[data_IDF["nom"] == "N recycling rate of human excretion in urban area"]["Ile de France"].item()
                / 100
            )
            N_prop_recy_rur_IDF = (
                data_IDF[data_IDF["nom"] == "N recycling rate of human excretion in rural area"]["Ile de France"].item()
                / 100
            )
            return (
                factor * pop_IDF * N_cons_cap_IDF * prop_urb_IDF * N_prop_recy_urb_IDF,
                factor * pop_IDF * N_cons_cap_IDF * (1 - prop_urb_IDF) * N_prop_recy_rur_IDF,
            )

        FE_N_N02_em = 0.002
        FE_N_NH3_em = 0.118
        FE_N_N2_em = 0.425
        pop = data[data["index_excel"] == 5][region].item()
        prop_urb = data[data["nom"] == "Urban population"][region].item() / 100
        N_cons_cap = data[data["index_excel"] == 8][region].item()
        N_cap_vege = data[data["index_excel"] == 9][region].item()
        N_cap_viande = data[data["index_excel"] == 10][region].item()
        N_boue = pop * N_cons_cap
        N_vege = pop * N_cap_vege
        N_viande = pop * N_cap_viande
        # Et calcul rapide sur les ingestions de produits de la pêche
        N_fish = N_boue - N_vege - N_viande
        source = {"fishery products": N_fish}
        target = {"urban": prop_urb, "rural": 1 - prop_urb}
        flux_generator.generate_flux(source, target)

        # Revenons aux boues
        # data[data["nom"] == "Total per capita protein ingestion"][region].item() * pop Formule fausse dans PVAR
        # data[data["nom"] == "N Sludges to cropland"][region].item()
        prop_recy_urb = data[data["nom"] == "N recycling rate of human excretion in urban area"][region].item() / 100
        prop_recy_rur = data[data["nom"] == "N recycling rate of human excretion in rural area"][region].item() / 100

        Norm = sum(df_cultures["Area (ha)"] * df_cultures["Spreading Rate (%)"])
        # Création du dictionnaire target
        target_ependage = {
            culture: row["Area (ha)"] * row["Spreading Rate (%)"] / Norm for culture, row in df_cultures.iterrows()
        }

        N_supp_urb, N_supp_rur = compute_N_supp()

        source_boue = {
            "urban": prop_urb * N_boue * prop_recy_urb + N_supp_urb,
            "rural": (1 - prop_urb) * prop_recy_rur * N_boue + N_supp_rur,
        }

        flux_generator.generate_flux(source_boue, target_ependage)

        # Le reste est perdu dans l'environnement
        # Ajouter les fuites de N2O
        source = {
            "urban": N_boue * prop_urb * FE_N_N02_em,
            "rural": N_boue * (1 - prop_urb) * FE_N_N02_em,
        }
        target = {"N2O emission": 1}
        flux_generator.generate_flux(source, target)

        # Ajouter les fuites de NH3
        source = {
            "urban": N_boue * prop_urb * FE_N_NH3_em,
            "rural": N_boue * (1 - prop_urb) * FE_N_NH3_em,
        }
        target = {"NH3 volatilization": 1}
        flux_generator.generate_flux(source, target)

        # Ajouter les fuites de N2
        source = {
            "urban": N_boue * prop_urb * FE_N_N2_em,
            "rural": N_boue * (1 - prop_urb) * FE_N_N2_em,
        }
        target = {"atmospheric N2": 1}
        flux_generator.generate_flux(source, target)

        # Le reste est perdu dans l'hydroshere
        target = {"hydro-system": 1}
        source = {
            "urban": N_boue * prop_urb * (1 - prop_recy_urb - FE_N_N02_em - FE_N_NH3_em - FE_N_N2_em),
            "rural": N_boue * (1 - prop_urb) * (1 - prop_recy_rur - FE_N_NH3_em - FE_N_N02_em - FE_N_N2_em),
        }
        # Remplir la matrice d'adjacence
        flux_generator.generate_flux(source, target)

        # Azote excrété sur prairies
        # Production d'azote

        df_elevage["Edible Nitrogen (ktN)"] = df_elevage["Production"] * df_elevage["% edible"]
        df_elevage.loc["poultry", "Edible Nitrogen (ktN)"] += (
            data[data["index_excel"] == 1023][region].item() * data[data["index_excel"] == 1067][region].item() / 100
        )  # ajout des oeufs
        df_elevage.loc["bovines", "Edible Nitrogen (ktN)"] += (
            data[data["index_excel"] == 1024][region].item() * data[data["index_excel"] == 1068][region].item() / 100
        )  # ajout du lait de vache

        # Plus délicat pour les ovins/caprins car la production de lait est mélangée
        tete_ovins_femelle = data[data["index_excel"] == 1171][region].item()
        tete_caprins_femelle = data[data["index_excel"] == 1167][region].item()
        production_par_tete_caprins = 1000  # kg/tete vu sur internet
        production_par_tete_ovins = 300  # kg/tete vu sur internet
        df_elevage.loc["ovines", "Edible Nitrogen (ktN)"] += (
            0
            if (production_par_tete_ovins * tete_ovins_femelle + production_par_tete_caprins * tete_caprins_femelle)
            == 0
            else data[data["index_excel"] == 1025][region].item()
            * data[data["index_excel"] == 1069][region].item()
            / 100
            * production_par_tete_ovins
            * tete_ovins_femelle
            / (production_par_tete_ovins * tete_ovins_femelle + production_par_tete_caprins * tete_caprins_femelle)
        )  # ajout du lait de brebis
        df_elevage.loc["caprines", "Edible Nitrogen (ktN)"] += (
            0
            if (production_par_tete_ovins * tete_ovins_femelle + production_par_tete_caprins * tete_caprins_femelle)
            == 0
            else data[data["index_excel"] == 1025][region].item()
            * data[data["index_excel"] == 1069][region].item()
            / 100
            * production_par_tete_caprins
            * tete_caprins_femelle
            / (production_par_tete_ovins * tete_ovins_femelle + production_par_tete_caprins * tete_caprins_femelle)
        )  # ajout du lait de brebis

        df_elevage["Non Edible Nitrogen (ktN)"] = df_elevage["Production"] * df_elevage["% non edible"]

        index = [1241 + j for j in range(6)]
        selected_data = data[data["index_excel"].isin(index)]
        selected_data.loc[:, "nom"] = selected_data["nom"].apply(lambda x: x.split()[0])
        selected_data = selected_data.groupby("nom").agg({region: "sum", "index_excel": "first"}).reset_index()

        df_elevage["Excreted nitrogen (ktN)"] = selected_data.set_index("nom")[region]
        df_elevage["Ingestion (ktN)"] = (
            df_elevage["Excreted nitrogen (ktN)"]
            + df_elevage["Edible Nitrogen (ktN)"]
            + df_elevage["Non Edible Nitrogen (ktN)"]
        )

        index = [1250 + j * 14 for j in range(6)]
        selected_data = data[data["index_excel"].isin(index)][region]
        selected_data.index = df_elevage.index

        df_elevage["% excreted on grassland"] = selected_data

        index = [1251 + j * 14 for j in range(6)]
        selected_data = data[data["index_excel"].isin(index)][region]
        selected_data.index = df_elevage.index

        df_elevage["% excreted indoors"] = selected_data

        index = [1252 + j * 14 for j in range(6)]
        selected_data = data[data["index_excel"].isin(index)][region]
        selected_data.index = df_elevage.index

        df_elevage["% excreted indoors as slurry"] = selected_data

        # On ajouter la catégorie other manure dans la catégorie liter manure
        index = [1253 + j * 14 for j in range(6)]
        selected_data = data[data["index_excel"].isin(index)][region]
        selected_data.index = df_elevage.index

        df_elevage["% excreted indoors as slurry"] += selected_data

        index = [1254 + j * 14 for j in range(6)]
        selected_data = data[data["index_excel"].isin(index)][region]
        selected_data.index = df_elevage.index

        df_elevage["% excreted indoors as manure"] = selected_data

        # Calculer les poids pour chaque cible
        # Calcul de la surface totale pour les prairies
        total_surface = (
            df_cultures.loc["Alfalfa and clover", "Area (ha)"]
            + df_cultures.loc["Non-legume temporary meadow", "Area (ha)"]
            + df_cultures.loc["Natural meadow ", "Area (ha)"]
        )

        # Création du dictionnaire target
        target = {
            "Alfalfa and clover": df_cultures.loc["Alfalfa and clover", "Area (ha)"] / total_surface,
            "Non-legume temporary meadow": df_cultures.loc["Non-legume temporary meadow", "Area (ha)"] / total_surface,
            "Natural meadow ": df_cultures.loc["Natural meadow ", "Area (ha)"] / total_surface,
        }
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted on grassland"]
            / 100
            * (1 - df_elevage["N-NH3 EM. outdoor"] - df_elevage["N-N2O EM. outdoor"] - df_elevage["N-N2 EM. outdoor"])
        ).to_dict()

        flux_generator.generate_flux(source, target)

        # Le reste est émit dans l'atmosphere
        # N2
        target = {"atmospheric N2": 1}
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted on grassland"]
            / 100
            * df_elevage["N-N2 EM. outdoor"]
        ).to_dict()

        flux_generator.generate_flux(source, target)

        # NH3
        # 1 % est volatilisée de manière indirecte sous forme de N2O
        target = {"NH3 volatilization": 0.99, "N2O emission": 0.01}
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted on grassland"]
            / 100
            * df_elevage["N-NH3 EM. outdoor"]
        ).to_dict()

        flux_generator.generate_flux(source, target)

        # volat_N2O = (
        #     0.01
        #     * df_elevage["Excreted nitrogen (ktN)"]
        #     * df_elevage["% excreted on grassland"]
        #     / 100
        #     * df_elevage["N-NH3 EM. outdoor"]
        # )
        # N2O
        target = {"N2O emission": 1}
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted on grassland"]
            / 100
            * df_elevage["N-N2O EM. outdoor"]
        ).to_dict()

        flux_generator.generate_flux(source, target)

        ## Epandage sur champs

        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted indoors"]
            / 100
            * (
                df_elevage["% excreted indoors as manure"]
                / 100
                * (
                    1
                    - df_elevage["N-NH3 EM. manure indoor"]
                    - df_elevage["N-N2O EM. manure indoor"]
                    - df_elevage["N-N2 EM. manure indoor"]
                )
                + df_elevage["% excreted indoors as slurry"]
                / 100
                * (
                    1
                    - df_elevage["N-NH3 EM. slurry indoor"]
                    - df_elevage["N-N2O EM. slurry indoor"]
                    - df_elevage["N-N2 EM. slurry indoor"]
                )
            )
        ).to_dict()

        flux_generator.generate_flux(source, target_ependage)

        # Le reste part dans l'atmosphere

        # N2
        target = {"atmospheric N2": 1}
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted indoors"]
            / 100
            * (
                df_elevage["% excreted indoors as slurry"] / 100 * df_elevage["N-N2 EM. slurry indoor"]
                + df_elevage["% excreted indoors as manure"] / 100 * df_elevage["N-N2 EM. manure indoor"]
            )
        ).to_dict()

        flux_generator.generate_flux(source, target)

        # NH3
        # 1 % est volatilisée de manière indirecte sous forme de N2O
        target = {"NH3 volatilization": 0.99, "N2O emission": 0.01}
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted indoors"]
            / 100
            * (
                df_elevage["% excreted indoors as slurry"] / 100 * df_elevage["N-NH3 EM. slurry indoor"]
                + df_elevage["% excreted indoors as manure"] / 100 * df_elevage["N-NH3 EM. manure indoor"]
            )
        ).to_dict()

        flux_generator.generate_flux(source, target)

        # volat_N2O = (
        #     0.01
        #     * df_elevage["Excreted nitrogen (ktN)"]
        #     * df_elevage["% excreted indoors"]
        #     / 100
        #     * (
        #         df_elevage["% excreted indoors as slurry"] / 100 * df_elevage["N-NH3 EM. slurry indoor"]
        #         + df_elevage["% excreted indoors as manure"] / 100 * df_elevage["N-NH3 EM. manure indoor"]
        #     )
        # )
        # N2O
        target = {"N2O emission": 1}
        source = (
            df_elevage["Excreted nitrogen (ktN)"]
            * df_elevage["% excreted indoors"]
            / 100
            * (
                df_elevage["% excreted indoors as slurry"] / 100 * df_elevage["N-N2O EM. slurry indoor"]
                + df_elevage["% excreted indoors as manure"] / 100 * df_elevage["N-N2O EM. manure indoor"]
            )
        ).to_dict()

        flux_generator.generate_flux(source, target)

        ## Azote synthétique
        # Calcul de l'azote épendu par hectare
        def calculer_azote_ependu(culture):
            sources = self.betail + self.Pop + ["atmospheric N2", "N2O emission", "NH3 volatilization", "other sectors"]
            adj_matrix_df = pd.DataFrame(self.adjacency_matrix, index=self.labels, columns=self.labels)
            return adj_matrix_df.loc[sources, culture].sum()

        df_cultures["Total Non Synthetic Fertilizer Use (ktN)"] = df_cultures.index.map(calculer_azote_ependu)
        df_cultures["Surface Non Synthetic Fertilizer Use (kgN/ha)"] = df_cultures.apply(
            lambda row: row["Total Non Synthetic Fertilizer Use (ktN)"] / row["Area (ha)"] * 10**6
            if row["Area (ha)"] > 0 and row["Total Non Synthetic Fertilizer Use (ktN)"] > 0
            else 0,
            axis=1,
        )

        # Mécanisme d'héritage de l'azote en surplus des légumineuses
        df_cultures["Leguminous Nitrogen Surplus (ktN)"] = 0.0
        df_cultures.loc[self.legumineuses, "Leguminous Nitrogen Surplus (ktN)"] = (
            df_cultures.loc[self.legumineuses, "Total Non Synthetic Fertilizer Use (ktN)"]
            - df_cultures.loc[self.legumineuses, "Nitrogen Production (ktN)"]
        )

        # Distribution du surplus aux céréales
        total_surplus_azote = df_cultures.loc[self.legumineuses, "Leguminous Nitrogen Surplus (ktN)"].sum()
        total_surface_cereales = df_cultures.loc[
            (
                (df_cultures["Category"] == "cereals (excluding rice)")
                | (df_cultures.index.isin(["Straw", "Forage maize"]))
            ),
            "Area (ha)",
        ].sum()
        df_cultures["Leguminous heritage (ktN)"] = 0.0
        df_cultures.loc[
            (
                (df_cultures["Category"] == "cereals (excluding rice)")
                | (df_cultures.index.isin(["Straw", "Forage maize"]))
            ),
            "Leguminous heritage (ktN)",
        ] = (
            df_cultures.loc[
                (
                    (df_cultures["Category"] == "cereals (excluding rice)")
                    | (df_cultures.index.isin(["Straw", "Forage maize"]))
                ),
                "Area (ha)",
            ]
            / total_surface_cereales
            * total_surplus_azote
        )

        # Génération des flux pour l'héritage des légumineuses
        source_leg = (
            df_cultures.loc[df_cultures["Leguminous Nitrogen Surplus (ktN)"] > 0]["Leguminous Nitrogen Surplus (ktN)"]
            / df_cultures["Leguminous Nitrogen Surplus (ktN)"].sum()
        ).to_dict()
        target_leg = df_cultures["Leguminous heritage (ktN)"].to_dict()
        flux_generator.generate_flux(source_leg, target_leg)

        # Calcul de l'azote à épendre
        df_cultures["Raw Surface Synthetic Fertilizer Use (ktN/ha)"] = df_cultures.apply(
            lambda row: row["Surface Fertilization Need (kgN/ha)"]
            - row["Surface Non Synthetic Fertilizer Use (kgN/ha)"]
            - (row["Leguminous heritage (ktN)"] / row["Area (ha)"] * 1e6)
            if row["Area (ha)"] > 0
            else row["Surface Fertilization Need (kgN/ha)"] - row["Surface Non Synthetic Fertilizer Use (kgN/ha)"],
            axis=1,
        )
        df_cultures["Raw Surface Synthetic Fertilizer Use (ktN/ha)"] = df_cultures[
            "Raw Surface Synthetic Fertilizer Use (ktN/ha)"
        ].apply(lambda x: max(x, 0))
        df_cultures["Raw Total Synthetic Fertilizer Use (ktN)"] = (
            df_cultures["Raw Surface Synthetic Fertilizer Use (ktN/ha)"] * df_cultures["Area (ha)"] / 1e6
        )

        # Calcul de la quantité moyenne (kgN) d'azote synthétique épendu par hectare
        # Séparer les données en prairies et champs
        df_prairies = df_cultures[df_cultures.index.isin(prairies)].copy()
        df_champs = df_cultures[df_cultures.index.isin(cultures)].copy()

        moyenne_ponderee_prairies = (
            df_prairies["Raw Surface Synthetic Fertilizer Use (ktN/ha)"] * df_prairies["Area (ha)"]
        ).sum()  # / df_prairies['Surface'].sum()
        moyenne_ponderee_champs = (
            df_champs["Raw Surface Synthetic Fertilizer Use (ktN/ha)"] * df_champs["Area (ha)"]
        ).sum()  # / df_champs['Surface'].sum()

        moyenne_reel_champs = (
            data[data["index_excel"] == 27][region].item() * data[data["index_excel"] == 23][region].item()
        )
        moyenne_reel_prairies = (
            data[data["index_excel"] == 29][region].item() * data[data["index_excel"] == 22][region].item() / 10**6
        )

        df_prairies.loc[:, "Adjusted Total Synthetic Fertilizer Use (ktN)"] = moyenne_reel_prairies
        df_champs.loc[:, "Adjusted Total Synthetic Fertilizer Use (ktN)"] = (
            df_champs["Raw Total Synthetic Fertilizer Use (ktN)"] * moyenne_reel_champs / moyenne_ponderee_champs
        )

        self.gamma = moyenne_reel_champs / moyenne_ponderee_champs

        # Mise à jour de df_cultures

        df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"] = (
            df_champs["Adjusted Total Synthetic Fertilizer Use (ktN)"]
            .combine_first(df_prairies["Adjusted Total Synthetic Fertilizer Use (ktN)"])
            .reindex(df_cultures.index, fill_value=0)  # Remplissage des clés manquantes (les légumineuses) avec 0
        )

        ## Azote synthétique volatilisé par les terres
        # Est ce qu'il n'y a que l'azote synthétique qui est volatilisé ?
        coef_volat_NH3 = data[data["index_excel"] == 31][region].item() / 100
        coef_volat_N2O = 0.01

        # 1 % des emissions de NH3 du aux fert. synth sont volatilisées sous forme de N2O
        df_cultures["Volatilized Nitrogen N-NH3 (ktN)"] = (
            df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"] * 0.99 * coef_volat_NH3
        )
        df_cultures["Volatilized Nitrogen N-N2O (ktN)"] = df_cultures[
            "Adjusted Total Synthetic Fertilizer Use (ktN)"
        ] * (coef_volat_N2O + 0.01 * coef_volat_NH3)
        df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"] = df_cultures[
            "Adjusted Total Synthetic Fertilizer Use (ktN)"
        ] * (1 - coef_volat_NH3 - coef_volat_N2O)
        # La quantité d'azote réellement épendue est donc un peu plus faible car une partie est volatilisée

        source = {"Haber-Bosch": 1}
        target = df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"].to_dict()

        flux_generator.generate_flux(source, target)

        source = df_cultures["Volatilized Nitrogen N-NH3 (ktN)"].to_dict()
        target = {"NH3 volatilization": 1}

        flux_generator.generate_flux(source, target)

        source = df_cultures["Volatilized Nitrogen N-N2O (ktN)"].to_dict()
        target = {"N2O emission": 1}

        flux_generator.generate_flux(source, target)

        # A cela on ajoute les emissions indirectes de N2O lors de la fabrication des engrais
        # epend_tot_synt = (
        #     df_cultures["Volatilized Nitrogen N-NH3 (ktN)"]
        #     + df_cultures["Volatilized Nitrogen N-N2O (ktN)"]
        #     + df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"]
        # ).sum()
        epend_tot_synt = df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"].sum()
        coef_emis_N_N2O = data[data["index_excel"] == 32][region].item() / 100
        target = {"N2O emission": 1}
        source = {"Haber-Bosch": epend_tot_synt * coef_emis_N_N2O}

        flux_generator.generate_flux(source, target)

        # Azote issu de la partie non comestible des carcasses
        source_non_comestible = df_elevage["Non Edible Nitrogen (ktN)"].to_dict()
        target_other_sectors = {"other sectors": 1}
        flux_generator.generate_flux(source_non_comestible, target_other_sectors)

        # On va chercher les éventuelles corrections apportées par JLN (=0 si export, donc pas vraiment net...)
        import_feed = self.data_loader.get_import_feed(year, region)
        # Et la valeur net
        import_feed_net = data[data["index_excel"] == 1009][region].item()

        df_elevage_comp = df_elevage.copy()
        df_cons_vege = df_elevage.loc[df_elevage["Ingestion (ktN)"] > 10**-8, "Ingestion (ktN)"]

        # On ajoute l'ingestion humaine
        # Une ligne urban, une ligne rural. Cela simplifiera la distinction de regime si un jour c'est pertinent

        df_cons_vege.loc["urban"] = N_vege * prop_urb
        df_cons_vege.loc["rural"] = N_vege * (1 - prop_urb)

        # On distingue les imports feed et food #TODO dans l'optim
        import_food_net = df_cons_vege.sum() - df_cultures["Nitrogen Production (ktN)"].sum() - import_feed_net
        import_food = max(0, import_food_net)

        supp_export = 0
        if import_feed_net > df_elevage["Ingestion (ktN)"].sum():
            supp_export = import_feed_net - df_elevage["Ingestion (ktN)"].sum()  # On augmentera d'autant les exports
            import_feed_net = df_elevage["Ingestion (ktN)"].sum()

        if len(df_cons_vege) > 0:
            # Dictionnaire enregistrant toutes les cultures présentes dans le régime d'un élevage
            all_cultures_regime = {}
            for cons in df_cons_vege.index:
                cultures_name = set()
                for cultures_liste in regimes[cons].values():
                    cultures_name.update(cultures_liste)
                all_cultures_regime[cons] = cultures_name

            # Initialisation du problème
            prob = LpProblem("Allocation_Azote_Animaux", LpMinimize)

            # Variables de décision pour les allocations
            x_vars = LpVariable.dicts(
                "x",
                [(culture, cons) for culture in df_cultures.index for cons in df_cons_vege.index],
                lowBound=0,
                cat="Continuous",
            )

            # Variable de depassement des importations feed
            E_vars_feed = LpVariable.dicts(
                "E",
                [(cons, culture) for cons in df_cons_vege.index[:-2] for culture in all_cultures_regime[cons]],
                lowBound=0,
                cat="Continuous",
            )

            # Variables de déviation des régimes alimentaires
            delta_vars = LpVariable.dicts(
                "delta",
                [(cons, proportion) for cons in df_cons_vege.index for proportion in regimes[cons].keys()],
                lowBound=0,
                cat=LpContinuous,
            )

            # Variables de pénalité pour la concentration des allocations
            # penalite_vars = LpVariable.dicts(
            #     "penalite",
            #     [(culture, cons) for culture in df_cultures.index for cons in df_cons_vege.index],
            #     lowBound=0,
            #     cat=LpContinuous,
            # )

            # Variables de pénalité pour la distribution au sein des catégories
            penalite_culture_vars = LpVariable.dicts(
                "penalite_culture",
                [
                    (cons, proportion, culture)
                    for cons in df_cons_vege.index
                    for proportion in regimes[cons].keys()
                    for culture in regimes[cons][proportion]
                ],
                lowBound=0,
                cat=LpContinuous,
            )

            # Variables d'importation pour chaque élevage et catégorie
            I_vars_feed = LpVariable.dicts(
                "I",
                [(cons, culture) for cons in df_cons_vege.index[:-2] for culture in all_cultures_regime[cons]],
                lowBound=0,
                cat="Continuous",
            )

            # Variables d'importation pour chaque population et catégorie
            I_vars_food = LpVariable.dicts(
                "I",
                [(cons, culture) for cons in df_cons_vege.index[-2:] for culture in all_cultures_regime[cons]],
                lowBound=0,
                cat="Continuous",
            )

            # # Variables pour capturer les importations associées aux déviations négatives
            # delta_import_vars = LpVariable.dicts(
            #     "delta_import",
            #     [(cons, proportion) for cons in df_cons_vege.index for proportion in regimes[cons].keys()],
            #     lowBound=0,
            #     cat=LpContinuous,
            # )

            # Pondération pour le terme de pénalité
            poids_penalite_deviation = 10

            # poids_penalite = 0  # Ajustez ce poids selon vos préférences

            # Poids pour équilibrer la distribution des cultures dans les categories
            poids_penalite_culture = 0.5  # À ajuster selon vos préférences

            # Définir un poids élevé pour pénaliser les importations
            if int(year) > 1960:
                poids_exces_import = 1
                poids_import_food = 1e-2
            else:
                poids_exces_import = 1000.0  # Ajustez ce poids selon vos préférences
                poids_import_food = 1000.0

            # poids_delta_import = (
            #     0.5  # Poids supplémentaire pour orienter les importations pour minimiser les fortes déviations
            # )

            prob += (
                poids_penalite_deviation
                * lpSum(
                    delta_vars[(cons, proportion)] for cons in df_cons_vege.index for proportion in regimes[cons].keys()
                )
                # + poids_delta_import
                # * lpSum(
                #     delta_import_vars[(cons, proportion)]
                #     for cons in df_cons_vege.index
                #     for proportion in regimes[cons].keys()
                # )
                # + poids_penalite
                # * lpSum(penalite_vars[(culture, cons)] for culture in df_cultures.index for cons in df_cons_vege.index)
                + poids_penalite_culture
                * lpSum(
                    penalite_culture_vars[(cons, proportion, culture)]
                    for cons in df_cons_vege.index
                    for proportion in regimes[cons].keys()
                    for culture in regimes[cons][proportion]
                )
                + poids_exces_import
                * lpSum(
                    E_vars_feed[(cons, culture)]
                    for cons in df_cons_vege.index[:-2]
                    for culture in all_cultures_regime[cons]
                )
                + poids_import_food
                * lpSum(
                    I_vars_food[(cons, culture)]
                    for cons in df_cons_vege.index[-2:]
                    for culture in all_cultures_regime[cons]
                ),
                "Minimiser_Deviations_Penalties_Et_Excès_Importation",
            )

            # Les besoins en feed sont complétés par la prod locale, l'importation de feed (donnees GRAFS) et un eventuel import excedentaire
            for cons in df_cons_vege.index[:-2]:
                besoin = df_cons_vege.loc[cons]
                prob += (
                    lpSum(x_vars[(culture, cons)] for culture in df_cultures.index)
                    + lpSum(I_vars_feed[(cons, culture)] for culture in all_cultures_regime[cons])
                    + lpSum(E_vars_feed[(cons, culture)] for culture in all_cultures_regime[cons])
                    == besoin,
                    f"Besoin_{cons}",
                )

            # Les besoins en food sont complétés par la production locale et les imports de food
            for cons in df_cons_vege.index[-2:]:
                besoin = df_cons_vege.loc[cons]
                prob += (
                    lpSum(x_vars[(culture, cons)] for culture in df_cultures.index)
                    + lpSum(I_vars_food[(cons, culture)] for culture in all_cultures_regime[cons])
                    == besoin,
                    f"Besoin_{cons}",
                )

            # Cette contrainte assure que la somme de l'azote alloué de chaque culture aux différents types de consommateurs ne dépasse pas l'azote disponible pour cette culture.
            for culture in df_cultures.index:
                azote_disponible = df_cultures.loc[culture, "Nitrogen Production (ktN)"]
                prob += (
                    lpSum(x_vars[(culture, cons)] for cons in df_cons_vege.index) <= azote_disponible,
                    f"Disponibilite_{culture}",
                )

            # interdiction de consommation locale et d'import pour des cultures qui ne sont pas dans le feed regime
            for cons in df_cons_vege.index[:-2]:
                cultures_autorisees = set()
                for cultures_liste in regimes[cons].values():
                    cultures_autorisees.update(cultures_liste)
                for culture in df_cultures.index:
                    if culture not in cultures_autorisees:
                        prob += (
                            x_vars[(culture, cons)] == 0,
                            f"Culture_Non_Autorisee_{culture}_{cons}",
                        )
                        # Vérifier si la variable I_vars existe avant d'ajouter la contrainte
                        if (cons, culture) in I_vars_feed:
                            prob += (
                                I_vars_feed[(cons, culture)] == 0,
                                f"Import_Non_Autorise_{cons}_{culture}",
                            )
                        if (cons, culture) in E_vars_feed:
                            prob += (
                                E_vars_feed[(cons, culture)] == 0,
                                f"Import_excedentaire_Non_Autorise_{cons}_{culture}",
                            )

            # même chose pour food
            for cons in df_cons_vege.index[-2:]:
                cultures_autorisees = set()
                for cultures_liste in regimes[cons].values():
                    cultures_autorisees.update(cultures_liste)
                for culture in df_cultures.index:
                    if culture not in cultures_autorisees:
                        prob += (
                            x_vars[(culture, cons)] == 0,
                            f"Culture_Non_Autorisee_{culture}_{cons}",
                        )
                        # Vérifier si la variable I_vars existe avant d'ajouter la contrainte
                        if (cons, culture) in I_vars_food:
                            prob += (
                                I_vars_food[(cons, culture)] == 0,
                                f"Import_Non_Autorise_{cons}_{culture}",
                            )

            # Ces contraintes calculent les déviations entre les proportions effectives des catégories consommées par chaque élevage et les proportions initiales du régime alimentaire.
            for cons in df_cons_vege.index[:-2]:
                besoin = df_cons_vege.loc[cons]
                for proportion_initiale, cultures_liste in regimes[cons].items():
                    # Azote total des cultures dans la liste
                    azote_cultures = (
                        lpSum(x_vars[(culture, cons)] for culture in cultures_liste if culture in df_cultures.index)
                        + lpSum(I_vars_feed[(cons, culture)] for culture in cultures_liste)
                        + lpSum(E_vars_feed[(cons, culture)] for culture in cultures_liste)
                    )
                    proportion_effective = azote_cultures / besoin
                    # Déviation par rapport à la proportion initiale
                    delta_var = delta_vars[(cons, proportion_initiale)]
                    prob += (
                        proportion_effective - proportion_initiale <= delta_var,
                        f"Deviation_Plus_{cons}_{proportion_initiale}",
                    )
                    prob += (
                        proportion_initiale - proportion_effective <= delta_var,
                        f"Deviation_Moins_{cons}_{proportion_initiale}",
                    )

            # Pareil pour food
            for cons in df_cons_vege.index[-2:]:
                besoin = df_cons_vege.loc[cons]
                for proportion_initiale, cultures_liste in regimes[cons].items():
                    # Azote total des cultures dans la liste
                    azote_cultures = lpSum(
                        x_vars[(culture, cons)] for culture in cultures_liste if culture in df_cultures.index
                    ) + lpSum(I_vars_food[(cons, culture)] for culture in cultures_liste)
                    proportion_effective = azote_cultures / besoin
                    # Déviation par rapport à la proportion initiale
                    delta_var = delta_vars[(cons, proportion_initiale)]
                    prob += (
                        proportion_effective - proportion_initiale <= delta_var,
                        f"Deviation_Plus_{cons}_{proportion_initiale}",
                    )
                    prob += (
                        proportion_initiale - proportion_effective <= delta_var,
                        f"Deviation_Moins_{cons}_{proportion_initiale}",
                    )

            # Les importations normales de feed sont égales aux données de GRAFS
            prob += (
                lpSum(
                    I_vars_feed[(cons, culture)]
                    for cons in df_cons_vege.index[:-2]
                    for culture in all_cultures_regime[cons]
                )
                == import_feed,
                "Limite_Imports_Normaux",
            )

            # # Calcul de l'allocation cible (par exemple, allocation uniforme)
            # for culture in df_cultures.index:
            #     azote_disponible_culture = df_cultures.loc[culture, "Azote disponible"]
            #     allocation_cible = azote_disponible_culture / len(df_cons_vege.index)  # Allocation uniforme
            #     for cons in df_cons_vege.index:
            #         allocation_reelle = x_vars[(culture, cons)]
            #         # Pénalité est la valeur absolue de la différence entre l'allocation réelle et l'allocation cible
            #         prob += (
            #             allocation_reelle - allocation_cible <= penalite_vars[(culture, cons)],
            #             f"Penalite_Plus_{culture}_{cons}",
            #         )
            #         prob += (
            #             allocation_cible - allocation_reelle <= penalite_vars[(culture, cons)],
            #             f"Penalite_Moins_{culture}_{cons}",
            #         )

            # Pénaliser si on nourrit les animaux avec une seule culture dans chaque groupe de proportions
            for cons in df_cons_vege.index[:-2]:
                besoin = df_cons_vege.loc[cons]
                for proportion, cultures_liste in regimes[cons].items():
                    # Allocation totale pour ce groupe de cultures
                    allocation_groupe = (
                        lpSum(x_vars[(culture, cons)] for culture in cultures_liste if culture in df_cultures.index)
                        + lpSum(I_vars_feed[(cons, culture)] for culture in cultures_liste)
                        + lpSum(E_vars_feed[(cons, culture)] for culture in cultures_liste)
                    )
                    # Azote total disponible pour ce groupe de cultures
                    azote_total_groupe = df_cultures.loc[
                        df_cultures.index.isin(cultures_liste),
                        "Nitrogen Production (ktN)",
                    ].sum()
                    if azote_total_groupe > 0:
                        for culture in cultures_liste:
                            if culture in df_cultures.index:
                                azote_disponible_culture = df_cultures.loc[culture, "Nitrogen Production (ktN)"]
                                # Calcul de l'allocation cible proportionnelle à la disponibilité
                                allocation_cible_culture = (
                                    azote_disponible_culture / azote_total_groupe
                                ) * allocation_groupe
                                # Allocation réelle
                                allocation_reelle_culture = x_vars[(culture, cons)]
                                # Pénalités pour la déviation
                                prob += (
                                    allocation_reelle_culture - allocation_cible_culture
                                    <= penalite_culture_vars[(cons, proportion, culture)],
                                    f"Penalite_Culture_Plus_{cons}_{proportion}_{culture}",
                                )
                                prob += (
                                    allocation_cible_culture - allocation_reelle_culture
                                    <= penalite_culture_vars[(cons, proportion, culture)],
                                    f"Penalite_Culture_Moins_{cons}_{proportion}_{culture}",
                                )
                    else:
                        pass

            # Pareil pour les humains
            for cons in df_cons_vege.index[-2:]:
                besoin = df_cons_vege.loc[cons]
                for proportion, cultures_liste in regimes[cons].items():
                    # Allocation totale pour ce groupe de cultures
                    allocation_groupe = lpSum(
                        x_vars[(culture, cons)] for culture in cultures_liste if culture in df_cultures.index
                    ) + lpSum(I_vars_food[(cons, culture)] for culture in cultures_liste)
                    # Azote total disponible pour ce groupe de cultures
                    azote_total_groupe = df_cultures.loc[
                        df_cultures.index.isin(cultures_liste),
                        "Nitrogen Production (ktN)",
                    ].sum()
                    if azote_total_groupe > 0:
                        for culture in cultures_liste:
                            if culture in df_cultures.index:
                                azote_disponible_culture = df_cultures.loc[culture, "Nitrogen Production (ktN)"]
                                # Calcul de l'allocation cible proportionnelle à la disponibilité
                                allocation_cible_culture = (
                                    azote_disponible_culture / azote_total_groupe
                                ) * allocation_groupe
                                # Allocation réelle
                                allocation_reelle_culture = x_vars[(culture, cons)]
                                # Pénalités pour la déviation
                                prob += (
                                    allocation_reelle_culture - allocation_cible_culture
                                    <= penalite_culture_vars[(cons, proportion, culture)],
                                    f"Penalite_Culture_Plus_{cons}_{proportion}_{culture}",
                                )
                                prob += (
                                    allocation_cible_culture - allocation_reelle_culture
                                    <= penalite_culture_vars[(cons, proportion, culture)],
                                    f"Penalite_Culture_Moins_{cons}_{proportion}_{culture}",
                                )
                    else:
                        pass

            # Contrainte pour importer le feed là où les déviations sont les plus importantes
            for cons in df_cons_vege.index[:-2]:
                for proportion, cultures_liste in regimes[cons].items():
                    # Total des importations pour cette proportion
                    azote_importe = lpSum(
                        I_vars_feed[(cons, culture)] + E_vars_feed[(cons, culture)]
                        for culture in cultures_liste
                        if culture in df_cultures.index
                    )
                    # # Lier aux variables de déviation
                    # prob += (
                    #     delta_import_vars[(cons, proportion)]
                    #     >= azote_importe - delta_vars[(cons, proportion)] * df_cons_vege.loc[cons],
                    #     f"Delta_Import_Lien_{cons}_{proportion}",
                    # )

            # Pareil pour les humains
            for cons in df_cons_vege.index[-2:]:
                for proportion, cultures_liste in regimes[cons].items():
                    # Total des importations pour cette proportion
                    azote_importe = lpSum(
                        I_vars_food[(cons, culture)] for culture in cultures_liste if culture in df_cultures.index
                    )
                    # # Lier aux variables de déviation
                    # prob += (
                    #     delta_import_vars[(cons, proportion)]
                    #     >= azote_importe - delta_vars[(cons, proportion)] * df_cons_vege.loc[cons],
                    #     f"Delta_Import_Lien_{cons}_{proportion}",
                    # )

            # Résolution du problème
            prob.solve()

            allocations = []
            for var in prob.variables():
                if var.name.startswith("x") and var.varValue > 0:
                    # Nom de la variable : x_(culture, cons)
                    chaine = str(var)
                    matches = re.findall(r"'([^']*)'", chaine)
                    parts = [match.replace("_", " ").strip() for match in matches]
                    culture = parts[0]
                    # Gestion du tiret dans le nom
                    if culture == "Non legume temporary meadow":
                        culture = "Non-legume temporary meadow"
                    if culture == "Natural meadow":
                        culture = "Natural meadow "
                    cons = parts[1]
                    if any(index in var.name for index in df_elevage.index):
                        Type = "Local culture feed"
                    else:
                        Type = "Local culture food"
                    allocations.append(
                        {
                            "Culture": culture,
                            "Consumer": cons,
                            "Allocated Nitrogen": var.varValue,
                            "Type": Type,
                        }
                    )
                elif var.name.startswith("I") and var.varValue > 0:
                    # Nom de la variable : I_(cons, culture)
                    chaine = str(var)
                    matches = re.findall(r"'([^']*)'", chaine)
                    parts = [match.replace("_", " ").strip() for match in matches]
                    cons = parts[0]
                    culture = parts[1]
                    if culture == "Non legume temporary meadow":
                        culture = "Non-legume temporary meadow"
                    if culture == "Natural meadow":
                        culture = "Natural meadow "
                    if any(index in var.name for index in df_elevage.index):
                        Type = "Imported Feed"
                    else:
                        Type = "Imported Food"
                    allocations.append(
                        {
                            "Culture": culture,
                            "Consumer": cons,
                            "Allocated Nitrogen": var.varValue,
                            "Type": Type,
                        }
                    )

                elif var.name.startswith("E") and var.varValue > 0:
                    # Nom de la variable : E_(cons, culture)
                    chaine = str(var)
                    matches = re.findall(r"'([^']*)'", chaine)
                    parts = [match.replace("_", " ").strip() for match in matches]
                    cons = parts[0]
                    culture = parts[1]
                    if culture == "Non legume temporary meadow":
                        culture = "Non-legume temporary meadow"
                    if culture == "Natural meadow":
                        culture = "Natural meadow "
                    allocations.append(
                        {
                            "Culture": culture,
                            "Consumer": cons,
                            "Allocated Nitrogen": var.varValue,
                            "Type": "Excess feed imports",
                        }
                    )

            allocations_df = pd.DataFrame(allocations)

            # Filtrer les lignes en supprimant celles dont 'Allocated Nitrogen' est très proche de zéro
            allocations_df = allocations_df[allocations_df["Allocated Nitrogen"].abs() >= 1e-6]

            self.allocation_vege = allocations_df

            # Extraction des déviations avec le signe
            deviations = []
            for cons in df_cons_vege.index[:-2]:
                for proportion in regimes[cons].keys():
                    proportion_rounded = round(proportion, 5)
                    delta_var_key = (cons, proportion_rounded)
                    deviation = delta_vars[delta_var_key].varValue
                    if deviation != 0:
                        # Récupérer la liste des cultures associées à cette proportion
                        cultures_liste = regimes[cons][proportion]
                        cultures_str = ", ".join(cultures_liste)

                        # Calcul de l'allocation totale (local et importée)
                        azote_cultures_feed = (
                            sum(
                                x_vars[(culture, cons)].varValue
                                for culture in cultures_liste
                                if (culture, cons) in x_vars
                            )
                            + sum(
                                I_vars_feed[(cons, culture)].varValue
                                for culture in cultures_liste
                                if (cons, culture) in I_vars_feed
                            )
                            + sum(
                                E_vars_feed[(cons, culture)].varValue
                                for culture in cultures_liste
                                if (cons, culture) in E_vars_feed
                            )
                        )
                        besoin_total = df_cons_vege.loc[cons]

                        # Calcul de la proportion effective
                        proportion_effective = azote_cultures_feed / besoin_total if besoin_total > 0 else 0

                        # Déterminer le signe
                        signe = 1 if proportion_effective > proportion else -1

                        deviations.append(
                            {
                                "Consumer": cons,
                                "Expected Proportion (%)": proportion_rounded * 100,
                                "Deviation (%)": signe * round(deviation, 4) * 100,  # Convertir en pourcentage
                                "Porportion Allocated (%)": proportion_rounded * 100
                                + signe * round(deviation, 4) * 100,
                                "Cultures": cultures_str,
                            }
                        )
            for cons in df_cons_vege.index[-2:]:
                for proportion in regimes[cons].keys():
                    proportion_rounded = round(proportion, 5)
                    delta_var_key = (cons, proportion_rounded)
                    deviation = delta_vars[delta_var_key].varValue
                    if deviation != 0:
                        # Récupérer la liste des cultures associées à cette proportion
                        cultures_liste = regimes[cons][proportion]
                        cultures_str = ", ".join(cultures_liste)

                        # Calcul de l'allocation totale (local et importée)
                        azote_cultures_food = sum(
                            x_vars[(culture, cons)].varValue for culture in cultures_liste if (culture, cons) in x_vars
                        ) + sum(
                            I_vars_food[(cons, culture)].varValue
                            for culture in cultures_liste
                            if (cons, culture) in I_vars_food
                        )
                        besoin_total = df_cons_vege.loc[cons]

                        # Calcul de la proportion effective
                        proportion_effective = azote_cultures_food / besoin_total if besoin_total > 0 else 0

                        # Déterminer le signe
                        signe = 1 if proportion_effective > proportion else -1

                        deviations.append(
                            {
                                "Consumer": cons,
                                "Expected Proportion (%)": proportion_rounded * 100,
                                "Deviation (%)": signe * round(deviation, 4) * 100,  # Convertir en pourcentage
                                "Porportion Allocated (%)": proportion_rounded * 100
                                + signe * round(deviation, 4) * 100,
                                "Cultures": cultures_str,
                            }
                        )
            self.deviations_df = pd.DataFrame(deviations)

            # Extraction des importations normales
            importations = []
            for cons in df_cons_vege.index[:-2]:
                for culture in all_cultures_regime[cons]:
                    if (cons, culture) in I_vars_feed:
                        import_value = I_vars_feed[(cons, culture)].varValue
                        if import_value > 0:
                            importations.append(
                                {
                                    "Consumer": cons,
                                    "Culture": culture,
                                    "Type": "Normal feed",
                                    "Imported Nitrogen (ktN)": import_value,
                                }
                            )
            for cons in df_cons_vege.index[-2:]:
                for culture in all_cultures_regime[cons]:
                    if (cons, culture) in I_vars_food:
                        import_value = I_vars_food[(cons, culture)].varValue
                        if import_value > 0:
                            importations.append(
                                {
                                    "Consumer": cons,
                                    "Culture": culture,
                                    "Type": "Normal food",
                                    "Imported Nitrogen (ktN)": import_value,
                                }
                            )

            # Extraction des imports excédentaires
            for cons in df_cons_vege.index[:-2]:
                for culture in all_cultures_regime[cons]:
                    if (cons, culture) in E_vars_feed:
                        excess_value = E_vars_feed[(cons, culture)].varValue
                        if excess_value > 0:
                            importations.append(
                                {
                                    "Consumer": cons,
                                    "Culture": culture,
                                    "Type": "Excédentaire feed",
                                    "Imported Nitrogen (ktN)": excess_value,
                                }
                            )

            # Convertir en DataFrame
            self.importations_df = pd.DataFrame(importations)

            # Calcul de la quantité d'azote importé non utilisée
            azote_importe_alloue = allocations_df[
                allocations_df["Type"].isin(["Imported Feed", "Imported Food", "Excess feed imports"])
            ]["Allocated Nitrogen"].sum()

            # Mise à jour de df_cultures
            for idx, row in df_cultures.iterrows():
                culture = row.name
                azote_alloue = allocations_df[
                    (allocations_df["Culture"] == culture)
                    & (allocations_df["Type"].isin(["Local culture food", "Local culture feed"]))
                ]["Allocated Nitrogen"].sum()
                azote_alloue_feed = allocations_df[
                    (allocations_df["Culture"] == culture) & (allocations_df["Type"] == "Local culture feed")
                ]["Allocated Nitrogen"].sum()
                azote_alloue_food = allocations_df[
                    (allocations_df["Culture"] == culture) & (allocations_df["Type"] == "Local culture food")
                ]["Allocated Nitrogen"].sum()
                df_cultures.loc[idx, "Available Nitrogen After Feed and Food (ktN)"] = (
                    row["Nitrogen Production (ktN)"] - azote_alloue
                )
                df_cultures.loc[idx, "Nitrogen For Feed (ktN)"] = azote_alloue_feed
                df_cultures.loc[idx, "Nitrogen For Food (ktN)"] = azote_alloue_food
            # Correction des valeurs proches de zéro
            df_cultures["Available Nitrogen After Feed and Food (ktN)"] = df_cultures[
                "Available Nitrogen After Feed and Food (ktN)"
            ].apply(lambda x: 0 if abs(x) < 1e-6 else x)
            df_cultures["Nitrogen For Feed (ktN)"] = df_cultures["Nitrogen For Feed (ktN)"].apply(
                lambda x: 0 if abs(x) < 1e-6 else x
            )
            df_cultures["Nitrogen For Food (ktN)"] = df_cultures["Nitrogen For Food (ktN)"].apply(
                lambda x: 0 if abs(x) < 1e-6 else x
            )

            # Mise à jour de df_elevage
            # Calcul de l'azote total alloué à chaque élevage
            azote_alloue_elevage = (
                allocations_df.groupby(["Consumer", "Type"])["Allocated Nitrogen"].sum().unstack(fill_value=0)
            )

            # Sélectionner uniquement les élevages (présents dans la liste `betail`)
            azote_alloue_elevage = azote_alloue_elevage.loc[
                azote_alloue_elevage.index.get_level_values("Consumer").isin(betail)
            ]

            # Ajouter les colonnes d'azote alloué dans df_elevage
            df_elevage.loc[:, "Consummed nitrogen from local feed (ktN)"] = df_elevage.index.map(
                azote_alloue_elevage.get("Local culture feed", pd.Series(0, index=df_elevage.index))
            )
            df_elevage.loc[:, "Consummed Nitrogen from imported feed (ktN)"] = df_elevage.index.map(
                lambda elevage: azote_alloue_elevage.get("Imported Feed", pd.Series(0, index=df_elevage.index)).get(
                    elevage, 0
                )
                + azote_alloue_elevage.get("Excess feed imports", pd.Series(0, index=df_elevage.index)).get(elevage, 0)
            )
            # df_elevage['Azote alloué importations'] = df_elevage.index.map(azote_alloue_elevage['Importation'])

            # Génération des flux pour les cultures locales
            allocations_locales = allocations_df[
                allocations_df["Type"].isin(["Local culture food", "Local culture feed"])
            ]

            for cons in df_cons_vege.index:
                target = {cons: 1}
                source = (
                    allocations_locales[allocations_locales["Consumer"] == cons]
                    .set_index("Culture")["Allocated Nitrogen"]
                    .to_dict()
                )
                if source:
                    flux_generator.generate_flux(source, target)

            # Génération des flux pour les importations
            allocations_imports = allocations_df[
                allocations_df["Type"].isin(["Imported Feed", "Imported Food", "Excess feed imports"])
            ]

            for cons in df_cons_vege.index:
                target = {cons: 1}
                cons_vege_imports = allocations_imports[allocations_imports["Consumer"] == cons]

                # Initialisation d'un dictionnaire pour collecter les flux par catégorie
                flux = {}

                for _, row in cons_vege_imports.iterrows():
                    culture = row["Culture"]
                    azote_alloue = row["Allocated Nitrogen"]

                    # Récupération de la catégorie de la culture
                    categorie = df_cultures.loc[culture, "Category"]

                    # Construction du label source pour l'importation
                    if cons in ["urban", "rural"]:
                        label_source = f"{categorie} food trade"
                    else:
                        label_source = f"{categorie} feed trade"

                    # Accumuler les flux par catégorie
                    if label_source in flux:
                        flux[label_source] += azote_alloue
                    else:
                        flux[label_source] = azote_alloue

                # Génération des flux pour l'élevage
                if sum(flux.values()) > 0:
                    flux_generator.generate_flux(flux, target)

            # On redonne à df_elevage sa forme d'origine et à import_feed_net sa vraie valeur
            # Utiliser `infer_objects(copy=False)` pour éviter l'avertissement sur le downcasting
            df_elevage = df_elevage.combine_first(df_elevage_comp)

            # Remplir les valeurs manquantes avec 0
            df_elevage = df_elevage.fillna(0)

            # Inférer les types pour éviter le warning sur les colonnes object
            df_elevage = df_elevage.infer_objects(copy=False)

            feed_export = import_feed - import_feed_net

            flux_exported = {}
            if feed_export > 10**-6:  # On a importé plus que les imports net, la diff est l'export de feed
                feed_export = min(
                    feed_export,
                    df_cultures["Available Nitrogen After Feed and Food (ktN)"].sum(),
                )  # Patch pour gérer les cas où on a une surexportation (cf Bretagne 2010)
                # On distingue les exports de feed prioritaires (prairies et fourrages) au reste
                # On distingue le cas où il y a assez dans les exports prioritaires pour couvrir
                # les export de feed au cas où il faut en plus exporter les autres cultures (mais d'abord les exports prio)
                if (
                    feed_export
                    > df_cultures.loc[
                        df_cultures["Category"].isin(["forages", "temporary meadows"]),
                        "Available Nitrogen After Feed and Food (ktN)",
                    ].sum()
                ):
                    feed_export_prio = df_cultures.loc[
                        df_cultures["Category"].isin(["forages", "temporary meadows"]),
                        "Available Nitrogen After Feed and Food (ktN)",
                    ].sum()
                    feed_export_other = feed_export - feed_export_prio
                else:
                    feed_export_prio = feed_export
                    feed_export_other = 0
                # Répartition de l'azote exporté inutilisé par catégorie
                # On fait un premier tour sur les cultures prioritaires
                for culture in df_cultures.loc[df_cultures["Category"].isin(["forages", "temporary meadows"])].index:
                    categorie = df_cultures.loc[df_cultures.index == culture, "Category"].item()
                    # On exporte pas en feed des catégories dédiées aux humains
                    if categorie not in ["rice", "fruits and vegetables", "roots"]:
                        # Calculer la quantité exportée par catégorie proportionnellement aux catégories présentes dans df_cultures
                        culture_nitrogen_available = df_cultures.loc[df_cultures.index == culture][
                            "Available Nitrogen After Feed and Food (ktN)"
                        ].item()

                        if culture_nitrogen_available > 0:
                            flux_exported[culture] = feed_export_prio * (
                                culture_nitrogen_available
                                / df_cultures["Available Nitrogen After Feed and Food (ktN)"].sum()
                            )

                # On écoule le reste des export de feed (si il y en a) sur les autres cultures
                if feed_export_other > 10**-6:
                    for culture in df_cultures.loc[
                        ~df_cultures["Category"].isin(["forages", "temporary meadows", "natural meadows "])
                    ].index:
                        categorie = df_cultures.loc[df_cultures.index == culture, "Category"].item()
                        # On exporte pas en feed des catégories dédiées aux humains
                        if categorie not in ["rice", "fruits and vegetables", "roots"]:
                            # Calculer la quantité exportée par catégorie proportionnellement aux catégories présentes dans df_cultures
                            culture_nitrogen_available = df_cultures.loc[df_cultures.index == culture][
                                "Available Nitrogen After Feed and Food (ktN)"
                            ].item()

                            if culture_nitrogen_available > 0:
                                flux_exported[culture] = feed_export_prio * (
                                    culture_nitrogen_available
                                    / df_cultures["Available Nitrogen After Feed and Food (ktN)"].sum()
                                )

                # Générer des flux les exportations vers leur catégorie d'origine
                for label_source, azote_exported in flux_exported.items():
                    if azote_exported > 0:
                        categorie = df_cultures.loc[df_cultures.index == label_source, "Category"].item()
                        label_target = f"{categorie} feed trade"
                        target = {label_target: 1}
                        source = {label_source: azote_exported}
                        flux_generator.generate_flux(source, target)

        # Mise à jour du DataFrame avec les quantités exportées
        df_cultures["Nitrogen Exported For Feed (ktN)"] = df_cultures.index.map(flux_exported).fillna(
            0
        )  # df_cultures.index.map(source).fillna(0)

        df_cultures["Available Nitrogen After Feed, Export Feed and Food (ktN)"] = (
            df_cultures["Available Nitrogen After Feed and Food (ktN)"]
            - df_cultures["Nitrogen Exported For Feed (ktN)"]
        ).apply(lambda x: 0 if abs(x) < 1e-6 else x)

        # import/export food
        # Le surplus est food exporté (ou stocké mais cela ne nous regarde pas)
        for idx, row in df_cultures.iterrows():
            culture = row.name
            categorie = df_cultures.loc[df_cultures.index == culture, "Category"].item()
            if categorie not in ["temporary meadows", "natural meadows ", "forages"]:
                source = {
                    culture: df_cultures.loc[
                        df_cultures.index == culture,
                        "Available Nitrogen After Feed, Export Feed and Food (ktN)",
                    ].item()
                }
                target = {f"{categorie} food trade": 1}
            elif (
                culture != "Natural meadow "
            ):  # TODO Que faire des production de feed qui ne sont ni consommées ni exportées ? Pour l'instant on les exporte....
                # Il faut les laisser retourner en terre si c'est une prairie naturelle (recommandation de JLN)
                source = {
                    culture: df_cultures.loc[
                        df_cultures.index == culture,
                        "Available Nitrogen After Feed, Export Feed and Food (ktN)",
                    ].item()
                }
                target = {f"{categorie} feed trade": 1}
            else:
                source = {
                    culture: df_cultures.loc[
                        df_cultures.index == culture,
                        "Available Nitrogen After Feed, Export Feed and Food (ktN)",
                    ].item()
                }
                target = {"soil stock": 1}
            flux_generator.generate_flux(source, target)

        # Que faire d'eventuel surplus de prairies ou forage ? Pour l'instant on les ignores... Ou alors vers soil stock ?

        ## Usage de l'azote animal pour nourir la population, on pourrait améliorer en distinguant viande, oeufs et lait

        viande_cap = data[data["index_excel"] == 10][region].item()
        cons_viande = viande_cap * pop

        # Reflechir a considerer un regime alimentaire carne (national) apres 1960
        if cons_viande < df_elevage["Edible Nitrogen (ktN)"].sum():  # Il y a assez de viande locale
            target = {
                "urban": prop_urb * cons_viande,
                "rural": (1 - prop_urb) * cons_viande,
            }
            source = (df_elevage["Edible Nitrogen (ktN)"] / df_elevage["Edible Nitrogen (ktN)"].sum()).to_dict()
            df_elevage["Net animal nitrogen exports (ktN)"] = df_elevage[
                "Edible Nitrogen (ktN)"
            ] - df_elevage.index.map(source) * sum(target.values())
            flux_generator.generate_flux(source, target)

        else:
            # On commence par consommer tout l'azote disponible
            target = {"urban": prop_urb, "rural": (1 - prop_urb)}
            source = df_elevage["Edible Nitrogen (ktN)"].to_dict()
            flux_generator.generate_flux(source, target)

            cons_viande_import = cons_viande - df_elevage["Edible Nitrogen (ktN)"].sum()
            commerce_path = "FAOSTAT_data_fr_viande_import.csv"
            commerce = pd.read_csv(os.path.join(self.data_loader.data_path, commerce_path))
            if (
                int(year) < 1965
            ):  # Si on est avant 65, on se base sur les rations de 65. De toute façon ça concerne des import minoritaires...
                year = "1965"
            commerce = commerce.loc[commerce["Année"] == int(year), ["Produit", "Valeur"]]

            corresp_dict = {
                "Viande, bovine, fraîche ou réfrigérée": "bovines",
                "Viande ovine, fraîche ou réfrigérée": "ovines",
                "Viande, caprin, fraîche ou réfrigérée": "caprines",
                "Viande, cheval, fraîche ou réfrigérée": "equine",
                "Viande, porc, fraîche ou réfrigérée": "porcines",
                "Viande, poulet, fraîche ou réfrigérée": "poultry",
            }

            commerce["Produit"] = commerce["Produit"].map(corresp_dict).fillna(commerce["Produit"])
            commerce["Ratio"] = commerce["Valeur"] / commerce["Valeur"].sum()
            commerce.index = commerce["Produit"]

            target = {
                "urban": prop_urb * cons_viande_import,
                "rural": (1 - prop_urb) * cons_viande_import,
            }
            source = {
                "animal trade": 1
            }  # commerce["Ratio"].to_dict() On peut distinguer les différents types d'azote importé
            flux_generator.generate_flux(source, target)
            # Et on reporte ce qu'il manque dans la colonne "Azote animal exporté net"
            df_elevage["Net animal nitrogen exports (ktN)"] = -commerce["Ratio"] * (cons_viande_import)

        if cons_viande < df_elevage["Edible Nitrogen (ktN)"].sum():
            source = df_elevage["Net animal nitrogen exports (ktN)"].to_dict()
            target = {"animal trade": 1}
            flux_generator.generate_flux(source, target)

        # Calcul des déséquilibres négatifs
        for label in cultures + legumineuses + prairies:
            node_index = label_to_index[label]
            row_sum = self.adjacency_matrix[node_index, :].sum()
            col_sum = self.adjacency_matrix[:, node_index].sum()
            imbalance = row_sum - col_sum  # Déséquilibre entre sorties et entrées
            if abs(imbalance) < 10**-6:
                imbalance = 0

            if (
                imbalance > 0
            ):  # Que conclure si il y a plus de sortie que d'entrée ? Que l'on détériore les réserves du sol ?
                # print(f"pb de balance avec {label}")
                # Plus de sorties que d'entrées, on augmente les entrées
                # new_adjacency_matrix[n, node_index] = imbalance  # Flux du nœud de balance vers la culture
                target = {label: imbalance}
                source = {"soil stock": 1}
                flux_generator.generate_flux(source, target)
            elif imbalance < 0:
                # Plus d'entrées que de sorties, on augmente les sorties
                # adjacency_matrix[node_index, n] = -imbalance  # Flux de la culture vers le nœud de balance
                if label != "Natural meadow ":  # 70% de l'excès fini dans les ecosystèmes aquatiques
                    source = {label: -imbalance}
                    # Ajouter soil stock parmis les surplus de fertilisation.
                    target = {
                        "other losses": 0.2925,
                        "hydro-system": 0.7,
                        "N2O emission": 0.0075,
                    }
                else:
                    if (
                        imbalance * 10**6 / df_cultures.loc[df_cultures.index == "Natural meadow ", "Area (ha)"].item()
                        > 100
                    ):  # Si c'est une prairie, l'azote est lessivé seulement au dela de 100 kgN/ha
                        source = {
                            label: -imbalance
                            - 100 * df_cultures.loc[df_cultures.index == "Natural meadow ", "Area (ha)"].item() / 10**6
                        }
                        target = {
                            "other losses": 0.2925,
                            "hydro-system": 0.7,
                            "N2O emission": 0.0075,
                        }
                        flux_generator.generate_flux(source, target)
                        source = {
                            label: 100
                            * df_cultures.loc[df_cultures.index == "Natural meadow ", "Area (ha)"].item()
                            / 10**6
                        }
                        target = {label: 1}
                    else:  # Autrement, l'azote reste dans le sol (cas particulier, est ce que cela a du sens, quid des autres cultures ?)
                        source = {label: -imbalance}
                        target = {"soil stock": 1}
                flux_generator.generate_flux(source, target)
            # Si imbalance == 0, aucun ajustement nécessaire

        # Calcul de imbalance dans df_cultures
        df_cultures["Balance (ktN)"] = (
            df_cultures["Adjusted Total Synthetic Fertilizer Use (ktN)"]
            + df_cultures["Total Non Synthetic Fertilizer Use (ktN)"]
            + df_cultures["Leguminous heritage (ktN)"]
            - df_cultures["Leguminous Nitrogen Surplus (ktN)"]
            - df_cultures["Nitrogen Production (ktN)"]
            - df_cultures["Volatilized Nitrogen N-NH3 (ktN)"]
            - df_cultures["Volatilized Nitrogen N-N2O (ktN)"]  # Pas de volat sous forme de N2 ?
        )

        # On équilibre Haber-Bosch avec atmospheric N2 pour le faire entrer dans le système
        target = {"Haber-Bosch": self.adjacency_matrix[label_to_index["Haber-Bosch"], :].sum()}
        source = {"atmospheric N2": 1}
        flux_generator.generate_flux(source, target)

        df_elevage["Conversion factor (%)"] = (
            df_elevage["Edible Nitrogen (ktN)"] + df_elevage["Non Edible Nitrogen (ktN)"]
        ) / df_elevage["Ingestion (ktN)"]

        from grafs_e.prospective import scenario

        LU = scenario.livestock_LU(self.data_loader, self.region)[self.year]
        LU["equine"] = LU.pop("equines")
        df_elevage["LU"] = LU

        # On ajoute une ligne total à df_cultures et df_elevage
        colonnes_a_exclure = [
            "Spreading Rate (%)",
            "Nitrogen Content (%)",
            "Seed input (kt seeds/kt Ymax)",
            "Category",
            "N fixation coef (kgN/kgN)",
            "Fertilization Need (kgN/qtl)",
            "Surface Fertilization Need (kgN/ha)",
            "Yield (qtl/ha)",
            "Yield (kgN/ha)",
            "Surface Non Synthetic Fertilizer Use (kgN/ha)",
            "Raw Surface Synthetic Fertilizer Use (ktN/ha)",
        ]
        colonnes_a_sommer = df_cultures.columns.difference(colonnes_a_exclure)
        total = df_cultures[colonnes_a_sommer].sum()
        total.name = "Total"
        self.df_cultures_display = pd.concat([df_cultures, total.to_frame().T])

        colonnes_a_exclure = [
            "% edible",
            "% excreted indoors",
            "% excreted indoors as manure",
            "% excreted indoors as slurry",
            "% excreted on grassland",
            "% non edible",
            "%N dairy",
            "N-N2 EM. manure indoor",
            "N-N2 EM. outdoor",
            "N-N2 EM. slurry indoor",
            "N-N2O EM. manure indoor",
            "N-N2O EM. outdoor",
            "N-N2O EM. slurry indoor",
            "N-NH3 EM. manure indoor",
            "N-NH3 EM. outdoor",
            "N-NH3 EM. slurry indoor",
            "Conversion factor (%)",
        ]
        colonnes_a_sommer = df_elevage.columns.difference(colonnes_a_exclure)
        total = df_elevage[colonnes_a_sommer].sum()
        total.name = "Total"
        self.df_elevage_display = pd.concat([df_elevage, total.to_frame().T])

        self.df_cultures = df_cultures
        self.df_elevage = df_elevage
        # self.adjacency_matrix = adjacency_matrix

    def get_df_culture(self):
        """
        Returns the DataFrame containing crop-related data.

        :return: A pandas DataFrame with crop data used in the nitrogen model.
        :rtype: pandas.DataFrame
        """
        return self.df_cultures

    def get_df_elevage(self):
        """
        Returns the DataFrame containing livestock-related data.

        :return: A pandas DataFrame with livestock data used in the nitrogen model.
        :rtype: pandas.DataFrame
        """
        return self.df_elevage

    def get_transition_matrix(self):
        """
        Returns the full nitrogen transition matrix.

        This matrix represents all nitrogen fluxes between sectors, including core and external processes.

        :return: A 2D NumPy array representing nitrogen fluxes between all sectors.
        :rtype: numpy.ndarray
        """
        return self.adjacency_matrix

    def get_core_matrix(self):
        """
        Extracts and returns the core matrix of nitrogen fluxes between active sectors.

        This method filters out rows and columns with no flows and excludes external sectors.
        The result isolates the central dynamics of the system.

        :return: A 2D NumPy array of the filtered core matrix.
        :rtype: numpy.ndarray
        """
        # Calcul de la taille du noyau
        core_size = len(self.adjacency_matrix) - len(self.ext)

        # Extraire la matrice principale (noyau)
        core_matrix = self.adjacency_matrix[:core_size, :core_size]

        # Calculer la somme des éléments sur chaque ligne
        row_sums = core_matrix.sum(axis=1)

        # Identifier les indices des lignes où la somme est non nulle
        non_zero_rows = row_sums != 0

        # Identifier les indices des colonnes à garder (les mêmes indices que les lignes non nulles)
        non_zero_columns = non_zero_rows

        # Filtrer les lignes et les colonnes avec une somme non nulle
        core_matrix_filtered = core_matrix[non_zero_rows, :][:, non_zero_columns]

        # Retourner la matrice filtrée
        self.core_matrix = core_matrix_filtered
        self.non_zero_rows = non_zero_rows
        return core_matrix_filtered

    def get_adjacency_matrix(self):
        """
        Returns the binary adjacency matrix of nitrogen fluxes.

        This matrix has the same dimensions as the core matrix and indicates the presence
        (1) or absence (0) of nitrogen fluxes between sectors.

        :return: A binary adjacency matrix.
        :rtype: numpy.ndarray
        """
        _ = self.get_core_matrix()
        return (self.core_matrix != 0).astype(int)

    def extract_input_output_matrixs(self, clean=True):
        """
        Extracts input and output matrices (C and B blocks) from the full transition matrix.

        These matrices represent the nitrogen flows between core and external sectors:
        - B: Outputs from core to external sectors.
        - C: Inputs from external to core sectors.

        If `clean` is True, the method removes rows and columns corresponding to inactive sectors.

        :param clean: Whether to remove zero-flow sectors from the matrices.
        :type clean: bool
        :return: A tuple (B, C) of NumPy arrays.
        :rtype: tuple[numpy.ndarray, numpy.ndarray]
        """
        # Fonction pour extraire la matrice entrée (C) et la matrice sortie (B) de la matrice complète.
        # Taille de la matrice coeur
        core_size = len(self.adjacency_matrix) - len(self.ext)
        n = len(self.adjacency_matrix)
        # Extraire la sous-matrice B (bloc haut-droit)
        B = self.adjacency_matrix[:core_size, core_size:n]

        # Extraire la sous-matrice C (bloc bas-gauche)
        C = self.adjacency_matrix[core_size:n, :core_size]

        if clean:
            C = C[:][:, self.non_zero_rows]
            B = B[self.non_zero_rows, :][:]

        return B, C

    def imported_nitrogen(self):
        """
        Calculates the total amount of nitrogen imported into the system.

        Includes nitrogen in imported food, feed, and excess feed.

        :return: Total imported nitrogen (in ktN).
        :rtype: float
        """
        return self.allocation_vege.loc[
            self.allocation_vege["Type"].isin(["Imported Food", "Imported Feed", "Excess feed imports"]),
            "Allocated Nitrogen",
        ].sum()

    def net_imported_plant(self):
        """
        Computes the net nitrogen imports for plant sectors.

        Calculated as the difference between total nitrogen imports and plant sector availability after local uses (feed and food).

        :return: Net nitrogen import for plant-based products (in ktN).
        :rtype: float
        """
        return (
            self.importations_df["Imported Nitrogen (ktN)"].sum()
            - self.df_cultures["Available Nitrogen After Feed and Food (ktN)"].sum()
        )

    def net_imported_animal(self):
        """
        Returns the net nitrogen export for animal sectors.

        :return: Total nitrogen exported via animal products (in ktN).
        :rtype: float
        """
        return self.df_elevage["Net animal nitrogen exports (ktN)"].sum()

    def total_plant_production(self):
        """
        Computes the total nitrogen production from all crop categories.

        :return: Total nitrogen produced by crops (in ktN).
        :rtype: float
        """
        return self.df_cultures["Nitrogen Production (ktN)"].sum()

    def stacked_plant_production(self):
        """
        Returns the vector of nitrogen production by crop category.

        :return: A pandas Series of nitrogen production per crop.
        :rtype: pandas.Series
        """
        return self.df_cultures["Nitrogen Production (ktN)"]

    def cereals_production(self):
        """
        Returns the nitrogen production from cereal crops.

        :return: Total nitrogen from cereals (in ktN).
        :rtype: float
        """
        return self.df_cultures.loc[
            self.df_cultures["Category"].isin(["cereals (excluding rice)", "rice"]), "Nitrogen Production (ktN)"
        ].sum()

    def leguminous_production(self):
        """
        Returns the nitrogen production from leguminous crops.

        :return: Total nitrogen from leguminous (in ktN).
        :rtype: float
        """
        return self.df_cultures.loc[
            self.df_cultures["Category"].isin(["leguminous"]), "Nitrogen Production (ktN)"
        ].sum()

    def oleaginous_production(self):
        """
        Returns the nitrogen production from oleaginous crops.

        :return: Total nitrogen from oleaginous (in ktN).
        :rtype: float
        """
        return self.df_cultures.loc[
            self.df_cultures["Category"].isin(["oleaginous"]), "Nitrogen Production (ktN)"
        ].sum()

    def grassland_and_forages_production(self):
        """
        Returns the nitrogen production from grassland and forages crops.

        :return: Total nitrogen from grassland and forages (in ktN).
        :rtype: float
        """
        return self.df_cultures.loc[
            self.df_cultures["Category"].isin(["temporary meadows", "natural meadows ", "forages"]),
            "Nitrogen Production (ktN)",
        ].sum()

    def roots_production(self):
        """
        Returns the nitrogen production from roots crops.

        :return: Total nitrogen from roots (in ktN).
        :rtype: float
        """
        return self.df_cultures.loc[self.df_cultures["Category"].isin(["roots"]), "Nitrogen Production (ktN)"].sum()

    def fruits_and_vegetable_production(self):
        """
        Returns the nitrogen production from fruits and vegetables crops.

        :return: Total nitrogen from fruits and vegetables (in ktN).
        :rtype: float
        """
        return self.df_cultures.loc[
            self.df_cultures["Category"].isin(["fruits and vegetables"]), "Nitrogen Production (ktN)"
        ].sum()

    def cereals_production_r(self):
        """
        Returns the share of nitrogen production from cereals relative to total plant production.

        :return: Percentage of total plant nitrogen production from cereals.
        :rtype: float
        """
        return (
            self.df_cultures.loc[
                self.df_cultures["Category"].isin(["cereals (excluding rice)", "rice"]), "Nitrogen Production (ktN)"
            ].sum()
            * 100
            / self.total_plant_production()
        )

    def leguminous_production_r(self):
        """
        Returns the share of nitrogen production from leguminous relative to total plant production.

        :return: Percentage of total plant nitrogen production from leguminous.
        :rtype: float
        """
        return (
            self.df_cultures.loc[self.df_cultures["Category"].isin(["leguminous"]), "Nitrogen Production (ktN)"].sum()
            * 100
            / self.total_plant_production()
        )

    def oleaginous_production_r(self):
        """
        Returns the share of nitrogen production from oleaginous relative to total plant production.

        :return: Percentage of total plant nitrogen production from oleaginous.
        :rtype: float
        """
        return (
            self.df_cultures.loc[self.df_cultures["Category"].isin(["oleaginous"]), "Nitrogen Production (ktN)"].sum()
            * 100
            / self.total_plant_production()
        )

    def grassland_and_forages_production_r(self):
        """
        Returns the share of nitrogen production from forages relative to total plant production.

        :return: Percentage of total plant nitrogen production from forages.
        :rtype: float
        """
        return (
            self.df_cultures.loc[
                self.df_cultures["Category"].isin(["temporary meadows", "natural meadows", "forages"]),
                "Nitrogen Production (ktN)",
            ].sum()
            * 100
            / self.total_plant_production()
        )

    def roots_production_r(self):
        """
        Returns the share of nitrogen production from roots relative to total plant production.

        :return: Percentage of total plant nitrogen production from roots.
        :rtype: float
        """
        return (
            self.df_cultures.loc[self.df_cultures["Category"].isin(["roots"]), "Nitrogen Production (ktN)"].sum()
            * 100
            / self.total_plant_production()
        )

    def fruits_and_vegetable_production_r(self):
        """
        Returns the share of nitrogen production from fruits and vegetables relative to total plant production.

        :return: Percentage of total plant nitrogen production from fruits and vegetables.
        :rtype: float
        """
        return (
            self.df_cultures.loc[
                self.df_cultures["Category"].isin(["fruits and vegetables"]), "Nitrogen Production (ktN)"
            ].sum()
            * 100
            / self.total_plant_production()
        )

    def animal_production(self):
        """
        Returns the total edible nitrogen produced by livestock sectors.

        :return: Total nitrogen in edible animal products (in ktN).
        :rtype: float
        """
        return self.df_elevage["Edible Nitrogen (ktN)"].sum()

    def emissions(self):
        """
        Computes the total nitrogen emissions from the system.

        Includes N₂O emissions, atmospheric N₂ release, and NH₃ volatilization, with unit conversions.

        :return: A pandas Series with nitrogen emission quantities.
        :rtype: pandas.Series
        """
        return pd.Series(
            {
                "N2O emission": np.round(
                    self.adjacency_matrix[:, label_to_index["N2O emission"]].sum() * (14 * 2 + 16) / (14 * 2), 2
                ),
                "atmospheric N2": np.round(self.adjacency_matrix[:, label_to_index["atmospheric N2"]].sum(), 2),
                "NH3 volatilization": np.round(
                    self.adjacency_matrix[:, label_to_index["NH3 volatilization"]].sum() * 17 / 14, 2
                ),
            },
            name="Emission",
        ).to_frame()["Emission"]

    def surfaces(self):
        """
        Returns the cultivated area per crop.

        :return: A pandas Series with area per crop (in hectares).
        :rtype: pandas.Series
        """
        return self.df_cultures["Area (ha)"]

    def surfaces_tot(self):
        """
        Returns the total cultivated area in the model.

        :return: Total area (in hectares).
        :rtype: float
        """
        return self.df_cultures["Area (ha)"].sum()

    def N_eff(self):
        return gr.GraphAnalyzer.calculate_Neff(self.adjacency_matrix)

    def C_eff(self):
        return gr.GraphAnalyzer.calculate_Ceff(self.adjacency_matrix)

    def F_eff(self):
        return gr.GraphAnalyzer.calculate_Feff(self.adjacency_matrix)

    def R_eff(self):
        return gr.GraphAnalyzer.calculate_Reff(self.adjacency_matrix)

    def Ftot(self, culture):
        area = self.df_cultures.loc[self.df_cultures.index == culture, "Area (ha)"].item()
        if area == 0:  # Vérification pour éviter la division par zéro
            return 0
        return self.adjacency_matrix[:, label_to_index[culture]].sum() * 1e6 / area

    def Y(self, culture):
        """
        Computes the nitrogen yield of a given crop.

        Yield is calculated as nitrogen production (kgN) per hectare for the specified crop.

        :param culture: The name of the crop (index of `df_cultures`).
        :type culture: str
        :return: Nitrogen yield in kgN/ha.
        :rtype: float
        """
        area = self.df_cultures.loc[self.df_cultures.index == culture, "Area (ha)"].item()
        if area == 0:  # Vérification pour éviter la division par zéro
            return 0
        return self.df_cultures.loc[self.df_cultures.index == culture, "Nitrogen Production (ktN)"].item() * 1e6 / area

    def tot_fert(self):
        """
        Computes total nitrogen inputs to the system, broken down by origin.

        Categories include animal and human excretion, atmospheric deposition, Haber-Bosch inputs, leguminous enrichment, etc.

        :return: A pandas Series of nitrogen inputs by source (in ktN).
        :rtype: pandas.Series
        """
        return pd.Series(
            {
                "Mining": self.adjacency_matrix[label_to_index["soil stock"], :].sum(),
                "Seeds": self.adjacency_matrix[label_to_index["other sectors"], :].sum(),
                "Human excretion": self.adjacency_matrix[
                    label_to_index["urban"] : label_to_index["rural"] + 1,
                    label_to_index["Wheat"] : label_to_index["Natural meadow "] + 1,
                ].sum(),
                "Leguminous soil enrichment": self.adjacency_matrix[
                    label_to_index["Horse beans and faba beans"] : label_to_index["Alfalfa and clover"] + 1,
                    label_to_index["Wheat"] : label_to_index["Natural meadow "] + 1,
                ].sum(),
                "Haber-Bosch": self.adjacency_matrix[label_to_index["Haber-Bosch"], :].sum(),
                "Atmospheric deposition": self.adjacency_matrix[
                    label_to_index["N2O emission"], : label_to_index["Natural meadow "] + 1
                ].sum()
                + self.adjacency_matrix[
                    label_to_index["NH3 volatilization"], : label_to_index["Natural meadow "] + 1
                ].sum(),
                "atmospheric N2": self.adjacency_matrix[
                    label_to_index["atmospheric N2"], label_to_index["Wheat"] : label_to_index["Natural meadow "] + 1
                ].sum(),
                "Animal excretion": self.adjacency_matrix[
                    label_to_index["bovines"] : label_to_index["equine"] + 1,
                    label_to_index["Wheat"] : label_to_index["Natural meadow "] + 1,
                ].sum(),
            }
        )

    def rel_fert(self):
        """
        Computes the relative share (%) of each nitrogen input source.

        :return: A pandas Series with nitrogen input sources as percentage of the total.
        :rtype: pandas.Series
        """
        df = self.tot_fert()
        return df * 100 / df.sum()

    def primXsec(self):
        """
        Calculates the percentage of nitrogen from secondary sources (biological or recycled),
        compared to the total nitrogen inputs.

        Secondary sources include: human excretion, animal excretion, atmospheric inputs, seeds, and leguminous fixation.

        :return: Share of secondary sources in total nitrogen inputs (%).
        :rtype: float
        """
        df = self.tot_fert()
        return (
            (
                df["Human excretion"].sum()
                + df["Animal excretion"].sum()
                + df["atmospheric N2"].sum()
                + df["Atmospheric deposition"].sum()
                + df["Seeds"].sum()
                + df["Leguminous soil enrichment"].sum()
            )
            * 100
            / df.sum()
        )

    def NUE(self):
        """
        Calculates the crop-level nitrogen use efficiency (NUE).

        Defined as the ratio of nitrogen produced by crops over total nitrogen inputs.

        :return: NUE of crop systems (%).
        :rtype: float
        """
        df = self.tot_fert()
        return self.df_cultures["Nitrogen Production (ktN)"].sum() * 100 / df.sum()

    def NUE_system(self):
        """
        Calculates system-wide nitrogen use efficiency, including crop and livestock production.

        Accounts for feed losses and nitrogen consumed via imported feed.

        :return: System-wide NUE (%).
        :rtype: float
        """
        N_NP = (
            self.df_cultures["Nitrogen Production (ktN)"].sum()
            - self.df_cultures["Nitrogen For Feed (ktN)"].sum()
            + self.df_elevage["Edible Nitrogen (ktN)"].sum()
            + self.df_elevage["Non Edible Nitrogen (ktN)"].sum()
        )
        df_fert = self.tot_fert()
        N_tot = (
            df_fert["Haber-Bosch"]
            + df_fert["atmospheric N2"]
            + df_fert["Atmospheric deposition"]
            + self.df_elevage["Consummed Nitrogen from imported feed (ktN)"].sum()
        )
        return N_NP / N_tot * 100

    def NUE_system_2(self):
        """
        Alternative NUE computation considering livestock conversion factors and feed inputs.

        Includes non-edible nitrogen outputs and imported feed consumption in the calculation.

        :return: Adjusted system-wide NUE (%).
        :rtype: float
        """
        N_NP = (
            self.df_cultures["Nitrogen Production (ktN)"].sum()
            + (
                (self.df_elevage["Edible Nitrogen (ktN)"] + self.df_elevage["Non Edible Nitrogen (ktN)"])
                * (1 - 1 / self.df_elevage["Conversion factor (%)"])
            ).sum()
            + self.df_elevage["Consummed Nitrogen from imported feed (ktN)"].sum()
        )
        df_fert = self.tot_fert()
        N_tot = (
            df_fert["Haber-Bosch"]
            + df_fert["atmospheric N2"]
            + df_fert["Atmospheric deposition"]
            + self.df_elevage["Consummed Nitrogen from imported feed (ktN)"].sum()
        )
        return N_NP / N_tot * 100

    def N_self_sufficient(self):
        """
        Estimates nitrogen self-sufficiency of the system.

        Defined as the share of atmospheric (biological) nitrogen inputs relative to all external nitrogen sources.

        :return: Self-sufficiency ratio (%).
        :rtype: float
        """
        df_fert = self.tot_fert()
        return (
            (df_fert["atmospheric N2"] + df_fert["Atmospheric deposition"])
            * 100
            / (
                df_fert["atmospheric N2"]
                + df_fert["Atmospheric deposition"]
                + df_fert["Haber-Bosch"]
                + self.df_elevage["Consummed Nitrogen from imported feed (ktN)"].sum()
            )
        )

    def env_footprint(self):
        """
        Calculates the land footprint (in ha) of nitrogen flows linked to:
        - local food and feed production,
        - imported food and feed,
        - imported and exported livestock nitrogen,
        - crop exports for feed and food.

        This is expressed as theoretical land areas mobilized by the nitrogen content.

        :return: A pandas Series of land footprint values (in ha), positive for imports and local use, negative for exports.
        :rtype: pandas.Series
        """
        local_surface_food = (
            self.df_cultures["Nitrogen For Food (ktN)"]
            / self.df_cultures["Nitrogen Production (ktN)"]
            * self.df_cultures["Area (ha)"]
        ).sum()
        local_surface_feed = (
            self.df_cultures["Nitrogen For Feed (ktN)"]
            / self.df_cultures["Nitrogen Production (ktN)"]
            * self.df_cultures["Area (ha)"]
        ).sum()

        # Food import
        # 1. Filtrer les allocations "Imported food"
        alloc = self.allocation_vege.loc[
            self.allocation_vege["Type"] == "Imported Food", ["Culture", "Allocated Nitrogen"]
        ]

        # 2. Grouper par culture au cas où il y aurait plusieurs lignes par culture
        alloc_grouped = alloc.groupby("Culture")["Allocated Nitrogen"].sum()

        # 3. Créer un DataFrame aligné avec les index de df_cultures
        alloc_df = pd.DataFrame(index=self.df_cultures.index)
        alloc_df["Allocated Nitrogen"] = alloc_grouped
        alloc_df["Allocated Nitrogen"] = alloc_df["Allocated Nitrogen"].fillna(0)

        # 4. Calcul final : ratio * surface
        # Récupère les valeurs de 'Nitrogen Production (ktN)' et de 'Allocated Nitrogen'
        nitrogen_production = self.df_cultures["Nitrogen Production (ktN)"]
        allocated_nitrogen = alloc_df["Allocated Nitrogen"]

        # Si 'Nitrogen Production (ktN)' est nul, se rabattre sur les valeurs du blé
        # En supposant que "Wheat" soit dans l'index de df_cultures, sinon adapte-le
        wheat_nitrogen_production = self.df_cultures.loc["Wheat", "Nitrogen Production (ktN)"]
        wheat_area = self.df_cultures.loc["Wheat", "Area (ha)"]

        # Remplacer les valeurs de 'Nitrogen Production (ktN)' par celles du blé si elles sont nulles
        adjusted_nitrogen_production = nitrogen_production.replace(0, wheat_nitrogen_production)

        # Utiliser la superficie du blé lorsque la production d'azote est nulle, sans modifier df_cultures
        adjusted_area = self.df_cultures["Area (ha)"].where(nitrogen_production != 0, wheat_area)

        # Calcul du total des importations alimentaires
        total_food_import = (allocated_nitrogen / adjusted_nitrogen_production * adjusted_area).sum()

        # Feed import
        # 1. Filtrer les allocations "Imported food"
        alloc = self.allocation_vege.loc[
            self.allocation_vege["Type"] == "Imported Feed", ["Culture", "Allocated Nitrogen"]
        ]

        # 2. Grouper par culture au cas où il y aurait plusieurs lignes par culture
        alloc_grouped = alloc.groupby("Culture")["Allocated Nitrogen"].sum()

        # 3. Créer un DataFrame aligné avec les index de df_cultures
        alloc_df = pd.DataFrame(index=self.df_cultures.index)
        alloc_df["Allocated Nitrogen"] = alloc_grouped
        alloc_df["Allocated Nitrogen"] = alloc_df["Allocated Nitrogen"].fillna(0)

        # 4. Calcul final : ratio * surface
        # Récupère les valeurs de 'Nitrogen Production (ktN)' et de 'Allocated Nitrogen'
        nitrogen_production = self.df_cultures["Nitrogen Production (ktN)"]
        allocated_nitrogen = alloc_df["Allocated Nitrogen"]

        # Si 'Nitrogen Production (ktN)' est nul, se rabattre sur les valeurs du blé
        # En supposant que "Wheat" soit dans l'index de df_cultures, sinon adapte-le
        wheat_nitrogen_production = self.df_cultures.loc["Wheat", "Nitrogen Production (ktN)"]
        wheat_area = self.df_cultures.loc["Wheat", "Area (ha)"]

        # Remplacer les valeurs de 'Nitrogen Production (ktN)' par celles du blé si elles sont nulles
        adjusted_nitrogen_production = nitrogen_production.replace(0, wheat_nitrogen_production)

        # Utiliser la superficie du blé lorsque la production d'azote est nulle, sans modifier df_cultures
        adjusted_area = self.df_cultures["Area (ha)"].where(nitrogen_production != 0, wheat_area)

        # Calcul du total des importations alimentaires
        total_feed_import = (allocated_nitrogen / adjusted_nitrogen_production * adjusted_area).sum()

        ## Importation de viande
        # 1. Sélectionner les animaux importés
        elevage_importe = self.df_elevage[self.df_elevage["Net animal nitrogen exports (ktN)"] < 0]

        # 2. Pourcentage importé = |export net négatif| / production totale
        elevage_importe["fraction_importée"] = (
            -elevage_importe["Net animal nitrogen exports (ktN)"] / elevage_importe["Edible Nitrogen (ktN)"]
        )

        # 3. Créer un DataFrame vide pour accumuler les contributions par culture
        surface_par_culture = pd.Series(0.0, index=self.df_cultures.index)

        # 4. Parcourir chaque type d'élevage importé
        for animal in elevage_importe.index:
            if animal not in self.allocation_vege["Consumer"].values:
                continue  # Si l'animal n'est pas dans les allocations, on passe

            # a. Calculer la part importée de l'azote pour cet élevage
            part_importee = elevage_importe.loc[animal, "fraction_importée"]

            if elevage_importe.loc[elevage_importe.index == animal, "fraction_importée"].item() == np.inf:
                # Calculer l'azote végétal nécessaire (N_feed=Azote importé/0.12)
                N_animal_imported = -elevage_importe.loc[animal, "Net animal nitrogen exports (ktN)"]
                N_feed_total_required = N_animal_imported / 0.12
                # Aller chercher dans régimes[animal] les cultures consommées et en quelles proportion
                # Dans chaque catégories, prendre la première culture avec un rendement non nul ou nan de la liste (df_cultures["Nitrogen Production (ktN)"]/df_culture["Area (ha)"])
                # En déduire la surface théoriquement utilisée pour le nourrir (surface_par_culture[culture] = N_feed/rendement)
                # Si aucune culture de la catégorie n'a de rendement, passer cette catégorie

                # Parcourir les catégories du régime de l'animal
                for proportion, culture_list in regimes[animal].items():
                    N_feed_for_category = N_feed_total_required * proportion

                    # Chercher la *première* culture valide dans la liste de la catégorie
                    for culture_name in culture_list:
                        # Vérifier si la culture existe dans df_cultures
                        if culture_name in self.df_cultures.index:
                            prod = self.df_cultures.loc[culture_name, "Nitrogen Production (ktN)"]
                            surface = self.df_cultures.loc[culture_name, "Area (ha)"]

                            # Calculer le rendement si possible (surface > 0 et prod > 0)
                            if surface > 0 and prod > 0:
                                rendement = prod / surface
                                # Calculer la surface nécessaire pour cette catégorie via cette culture
                                surface_needed = N_feed_for_category / rendement
                                # Ajouter à la surface totale pour cette culture
                                surface_par_culture[culture_name] = (
                                    surface_par_culture.get(culture_name, 0) + surface_needed
                                )
                                break  # On a trouvé la première culture valide, on passe à la catégorie suivante du régime
                            # else: rendement invalide (0 ou NaN), on essaie la culture suivante dans la liste
                        # else: la culture n'est pas dans df_cultures, on essaie la suivante dans la liste
            else:
                # b. Extraire les allocations d'azote de chaque culture pour cet élevage
                aliments = self.allocation_vege[self.allocation_vege["Consumer"] == animal]

                for _, row in aliments.iterrows():
                    culture = row["Culture"]
                    azote = row["Allocated Nitrogen"] * part_importee  # Quantité d'azote importée pour cette culture

                    if culture not in self.df_cultures.index:
                        culture = "Wheat"  # Si la culture n'est pas dans df_cultures, on remplace par du blé

                    # c. Récupérer la production d'azote et la surface de la culture
                    prod = self.df_cultures.loc[culture, "Nitrogen Production (ktN)"]
                    surface = self.df_cultures.loc[culture, "Area (ha)"]
                    # if prod == 0:
                    #     culture = "Wheat"
                    #     prod = self.df_cultures.loc[culture, "Nitrogen Production (ktN)"]
                    #     surface = self.df_cultures.loc[culture, "Area (ha)"]
                    # d. Calculer la surface nécessaire pour produire l'azote consommé
                    if prod > 0:
                        surface_equivalente = azote / prod * surface
                        surface_par_culture[culture] += surface_equivalente
        import_animal = surface_par_culture.sum()

        ## Export animaux
        # 1. Sélectionner les animaux exportés (ceux qui ont un exportation nette positive)
        elevage_exporte = self.df_elevage[self.df_elevage["Net animal nitrogen exports (ktN)"] > 0]

        # 2. Calculer la fraction exportée pour chaque animal (en proportion de la production totale)
        elevage_exporte["fraction_exportée"] = (
            elevage_exporte["Net animal nitrogen exports (ktN)"] / elevage_exporte["Edible Nitrogen (ktN)"]
        )

        # 3. Créer un dictionnaire pour accumuler les résultats par culture
        surface_par_culture_exporte = pd.Series({culture: 0.0 for culture in self.df_cultures.index})

        # 4. Parcourir chaque type d'élevage exporté
        for animal in elevage_exporte.index:
            if animal not in self.allocation_vege["Consumer"].values:
                continue  # Si l'animal n'est pas dans les allocations, on passe

            # a. Calculer la part exportée de l'azote pour cet élevage
            part_exportee = elevage_exporte.loc[animal, "fraction_exportée"]

            # b. Extraire les allocations d'azote de chaque culture pour cet élevage
            aliments = self.allocation_vege[self.allocation_vege["Consumer"] == animal]

            for _, row in aliments.iterrows():
                culture = row["Culture"]
                azote = row["Allocated Nitrogen"] * part_exportee  # Quantité d'azote exportée pour cette culture

                if culture not in self.df_cultures.index:
                    culture = "Wheat"  # Si la culture n'est pas dans df_cultures, on remplace par du blé

                # c. Récupérer la production d'azote et la surface de la culture
                prod = self.df_cultures.loc[culture, "Nitrogen Production (ktN)"]
                surface = self.df_cultures.loc[culture, "Area (ha)"]

                # d. Calculer la surface nécessaire pour produire l'azote consommé
                if prod > 0:
                    surface_equivalente = azote / prod * surface
                    surface_par_culture_exporte[culture] += surface_equivalente
        export_animal = surface_par_culture_exporte.sum()

        # Export culture
        # Feed
        export_surface_feed = (
            self.df_cultures["Nitrogen Exported For Feed (ktN)"]
            / self.df_cultures["Nitrogen Production (ktN)"]
            * self.df_cultures["Area (ha)"]
        ).sum()
        # Food
        export_surface_food = (
            self.df_cultures["Available Nitrogen After Feed, Export Feed and Food (ktN)"]
            / self.df_cultures["Nitrogen Production (ktN)"]
            * self.df_cultures["Area (ha)"]
        ).sum()
        return pd.Series(
            {
                "Local Food": int(local_surface_food),
                "Local Feed": int(local_surface_feed),
                "Import Food": int(total_food_import),
                "Import Feed": int(total_feed_import),
                "Import Livestock": int(import_animal),
                "Export Livestock": -int(export_animal),
                "Export Feed": -int(export_surface_feed),
                "Export Food": -int(export_surface_food),
            }
        )

    def net_footprint(self):
        """
        Computes the net nitrogen land footprint of the region (in Mha).

        Aggregates all imports and exports to yield a net balance of nitrogen-dependent land use.

        :return: Net land footprint (in million hectares).
        :rtype: float
        """
        df = self.env_footprint()
        df_total_import = df.loc[["Import Food", "Import Feed", "Import Livestock"]].sum(axis=0)
        df_total_export = df.loc[["Export Food", "Export Feed", "Export Livestock"]].sum(axis=0)
        net_import_export = df_total_import + df_total_export
        return np.round(net_import_export / 1e6, 2)

    def LU_density(self):
        """
        Calculates the livestock unit density over the agricultural area.

        :return: Livestock unit per hectare (LU/ha).
        :rtype: float
        """
        return np.round(self.df_elevage["LU"].sum() / self.df_cultures["Area (ha)"].sum(), 2)

    def NH3_vol(self):
        """
        Returns the total NH₃ volatilization in the system.

        :return: NH₃ emissions in kt.
        :rtype: float
        """
        return self.emissions()["NH3 volatilization"]

    def N2O_em(self):
        """
        Returns the total N₂O emissions in the system.

        :return: N₂O emissions in kt.
        :rtype: float
        """
        return self.emissions()["N2O emission"]


# Créer une instance du modèle
# year = "2010"
# region = "Bretagne"
# data = DataLoader()

# nitrogen_model = NitrogenFlowModel(
#     data=data,
#     year=year,
#     region=region,
#     categories_mapping=categories_mapping,
#     labels=labels,
#     cultures=cultures,
#     legumineuses=legumineuses,
#     prairies=prairies,
#     betail=betail,
#     Pop=Pop,
#     ext=ext,
# )

# from IPython import embed

# embed()

# # Calculer les flux
# nitrogen_model.compute_fluxes()

# # Afficher la heatmap
# nitrogen_model.plot_heatmap()
