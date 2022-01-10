import pandas as _pd
import numpy as _np
import datetime as _dt
import matplotlib.pyplot as plt


class SummaryInformation():
    """Display summary statistics in tabular form and plots of relevent data.

    """
    def __init__(self, dfs):

        self.dfs = dfs

    def admission_summary(self, from_date=None, to_date=None):

        from_date= _dt.datetime.strptime(from_date, '%Y-%m-%d')
        to_date= _dt.datetime.strptime(to_date, '%Y-%m-%d')

        if from_date is None:
            from_date = self.dfs['AdmissionsCorePopulatedTable']['AdmissionStartDate'].min()
        if to_date is None:
            to_date = self.dfs['AdmissionsCorePopulatedTable']['AdmissionStartDate'].max()

        diff = round(((to_date - from_date) / _np.timedelta64(1,'Y') / 71.65108517324487) * 10) + 5

        dates = ['AdmissionStartDate', 'AdmissionEndDate']
        for date in dates:
            self.dfs['AdmissionsCorePopulatedTable'][date] = _pd.to_datetime(self.dfs['AdmissionsCorePopulatedTable'][date])

        fig = plt.figure(figsize=(15,3))
        ax = fig.add_subplot()

        self.dfs['AdmissionsCorePopulatedTable'][(self.dfs['AdmissionsCorePopulatedTable']['AdmissionStartDate']> from_date) & (self.dfs['AdmissionsCorePopulatedTable']['AdmissionStartDate']< to_date)][['AdmissionStartDate']].groupby([self.dfs['AdmissionsCorePopulatedTable'].AdmissionStartDate.dt.year, self.dfs['AdmissionsCorePopulatedTable'].AdmissionStartDate.dt.year]).count().plot(kind="bar")

        return fig, ax


    def admission_time_diff_summary(self):

        fig = plt.figure(figsize=(12,3))
        ax = fig.add_subplot()

        self.dfs['AdmissionsCorePopulatedTable']['AdmissionDiff'] = self.dfs['AdmissionsCorePopulatedTable']['AdmissionEndDate'] - self.dfs['AdmissionsCorePopulatedTable']['AdmissionStartDate']
        self.dfs['AdmissionsCorePopulatedTable']['AdmissionDiff'] = self.dfs['AdmissionsCorePopulatedTable']['AdmissionDiff'] / _np.timedelta64(1,'D')
        self.dfs['AdmissionsCorePopulatedTable']['AdmissionDiff'].plot(kind='hist', ax=ax)

        return fig, ax

    def lab_summary(self, filter=['LabName', 'LabUnits'], dates=[None, None]):
        """Returns a dataframe of summary statistics for labtests in the dataset. Optionally the user can specify a date range for the dataset.

        Args:
            self.dfs ([pd.DataFrame]): The dataset to perform summary statistics on.
            filter (list, optional): Filters what the table will be grouped by. Defaults to ['LabName', 'LabUnits'].
            dates (list, optional): Specifies a date range for the dataset. Defaults to [None, None].

        Returns:
            [pd.DataFrame]: A dataframe of the summary statistics.
        """
        self.dfs['LabsCorePopulatedTable'] = self.dfs['LabsCorePopulatedTable'].set_index(['LabDateTime'])
        details = self.dfs['LabsCorePopulatedTable'].loc[dates].groupby(['LabName', 'LabUnits'])[['LabValue']].describe()


        return details


    def lab_plot(self):
        """A visualsation of the 'lab_summary()' function.

        Args:
            self.dfs ([pd.DataFrame]): The dataset to visualise the data from.

        Returns:
            [matplotlib]: box plots of lab summary statstics. 
        """
        labs = set(list(self.dfs['LabsCorePopulatedTable']['LabName']))
        fig, ax = plt.subplots(7, 5, figsize=(28,30))
        i, j = 0, 0
        for lab in labs:
            if i == 7:
                j += 1
                i = 0
            self.dfs['LabsCorePopulatedTable'][self.dfs['LabsCorePopulatedTable']['LabName'] == lab][['LabValue']].plot(kind='box', grid=True, ax=ax[i, j]).set_title(lab)
            i += 1

        return fig, ax


    def personal_plot(self):
        """Displays several barcharts of patient personal information (e.g. gender or race).

        Args:
            self.dfs ([pd.DataFrame]): The dataset to visualise the data from.

        Returns:
            [matplotlib]: plots of patients personal information. 
        """
        categorical_features = ['PatientGender', 'PatientRace', 'PatientMaritalStatus', 'PatientLanguage']
        fig, ax = plt.subplots(1, len(categorical_features), figsize=(10,8))
        for i, categorical_feature in enumerate(self.dfs['PatientCorePopulatedTable'][categorical_features]):
            self.dfs['PatientCorePopulatedTable'][categorical_feature].value_counts().plot(kind="bar", ax=ax[i]).set_title(categorical_feature)
        
        return fig, ax