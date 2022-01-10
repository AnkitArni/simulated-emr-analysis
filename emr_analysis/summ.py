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

    def lab_summary(self, from_date=None, to_date=None):
        """[summary]

        Args:
            from_date ([type], optional): [description]. Defaults to None.
            to_date ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        self.dfs['LabsCorePopulatedTable']['LabDateTime'] = _pd.to_datetime(self.dfs['LabsCorePopulatedTable']['LabDateTime'])

        from_date= _dt.datetime.strptime(from_date, '%Y-%m-%d')
        to_date= _dt.datetime.strptime(to_date, '%Y-%m-%d')

        if from_date is None:
            from_date = self.dfs['LabsCorePopulatedTable']['LabDateTime'].min()
        if to_date is None:
            to_date = self.dfs['LabsCorePopulatedTable']['LabDateTime'].max()

        details = self.dfs['LabsCorePopulatedTable'][(self.dfs['LabsCorePopulatedTable']['LabDateTime']> from_date) & (self.dfs['LabsCorePopulatedTable']['LabDateTime']< to_date)].groupby(['LabName', 'LabUnits'])[['LabValue']].describe()

        return details


    def lab_plot(self):
        """Displays a histogram for each lab test seprated by lab type.
        """
        for lab_type in {x.split(':')[0] for x in self.dfs['LabsCorePopulatedTable']['LabName']}:
    
            lab_fig_data = self.dfs['LabsCorePopulatedTable'][self.dfs['LabsCorePopulatedTable']['LabName'].str.contains(lab_type)]
            
            labs = set(list(lab_fig_data['LabName']))

            n = len(labs)
            j = 5
            i = round(n/j + .49)

            fig, ax = plt.subplots(i, j, figsize=(28,i*j))

            if i != 1:

                row, col = 0, 0
                for lab in labs:
                    if col == j:
                        col = 0
                        row += 1
                    lab_fig_data[lab_fig_data['LabName'] == lab][['LabValue']].plot(kind='hist', grid=True, ax=ax[row, col], xlabel='Test', ylabel='Test').set_title(lab)
                    col += 1

                if n % j != 0:
                    for k in range(5- (n % j)):
                        fig.delaxes(ax[i-1,j-1-k])

            else:
                
                for i, lab in enumerate(labs):
                    lab_fig_data[lab_fig_data['LabName'] == lab][['LabValue']].plot(kind='hist', grid=True, ax=ax[i], xlabel='Test', ylabel='Test').set_title(lab)

                if n % j != 0:
                    for k in range(5- (n % j)):
                        fig.delaxes(ax[j-1-k])

            fig.show()


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