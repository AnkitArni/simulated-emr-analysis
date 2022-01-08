import pandas as _pd
import numpy as _np
import matplotlib.pyplot as plt


class SummaryInformation:
    """Display summary statistics in tabular form and plots of relevent data.
    """
    def __init__(self):

        pass

    def lab_summary(self, dfs, filter=['LabName', 'LabUnits'], dates=[None, None]):
        """Returns a dataframe of summary statistics for labtests in the dataset. Optionally the user can specify a date range for the dataset.

        Args:
            dfs ([pd.DataFrame]): The dataset to perform summary statistics on.
            filter (list, optional): Filters what the table will be grouped by. Defaults to ['LabName', 'LabUnits'].
            dates (list, optional): Specifies a date range for the dataset. Defaults to [None, None].

        Returns:
            [pd.DataFrame]: A dataframe of the summary statistics.
        """
        dfs['LabsCorePopulatedTable'] = dfs['LabsCorePopulatedTable'].set_index(['LabDateTime'])
        details = dfs['LabsCorePopulatedTable'].loc[dates].groupby(['LabName', 'LabUnits'])[['LabValue']].describe()


        return details


    def lab_plot(self, dfs):
        """A visualsation of the 'lab_summary()' function.

        Args:
            dfs ([pd.DataFrame]): The dataset to visualise the data from.

        Returns:
            [matplotlib]: box plots of lab summary statstics. 
        """
        labs = set(list(dfs['LabsCorePopulatedTable']['LabName']))
        fig, ax = plt.subplots(7, 5, figsize=(28,30))
        i, j = 0, 0
        for lab in labs:
            if i == 7:
                j += 1
                i = 0
            dfs['LabsCorePopulatedTable'][dfs['LabsCorePopulatedTable']['LabName'] == lab][['LabValue']].plot(kind='box', grid=True, ax=ax[i, j]).set_title(lab)
            i += 1

        return fig, ax


    def personal_plot(self, dfs):
        """Displays several barcharts of patient personal information (e.g. gender or race).

        Args:
            dfs ([pd.DataFrame]): The dataset to visualise the data from.

        Returns:
            [matplotlib]: plots of patients personal information. 
        """
        categorical_features = ['PatientGender', 'PatientRace', 'PatientMaritalStatus', 'PatientLanguage']
        fig, ax = plt.subplots(1, len(categorical_features), figsize=(10,8))
        for i, categorical_feature in enumerate(dfs['PatientCorePopulatedTable'][categorical_features]):
            dfs['PatientCorePopulatedTable'][categorical_feature].value_counts().plot(kind="bar", ax=ax[i]).set_title(categorical_feature)
        
        return fig, ax