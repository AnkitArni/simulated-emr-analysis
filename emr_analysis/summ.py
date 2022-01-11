import pandas as _pd
import numpy as _np
import datetime as _dt
import matplotlib.pyplot as plt


class SummaryInformation():
    """Display summary statistics in tabular form and plots of relevent data.

    """
    def __init__(self, dfs):

        self.dfs = dfs

    def admission_plot(self, from_date=None, to_date=None):

        dates = ['AdmissionStartDate', 'AdmissionEndDate']

        for date in dates:
            self.dfs['admissions'][date] = _pd.to_datetime(self.dfs['admissions'][date])

        if from_date is None:
            from_date = self.dfs['admissions']['AdmissionStartDate'].min()
        else:
            from_date= _dt.datetime.strptime(from_date, '%Y-%m-%d')

        if to_date is None:
            to_date = self.dfs['admissions']['AdmissionStartDate'].max()
        else:
            to_date= _dt.datetime.strptime(to_date, '%Y-%m-%d')

        diff = round(((to_date - from_date) / _np.timedelta64(1,'Y') / 71.65108517324487) * 10) + 10

        fig = plt.figure(figsize=(diff,3))
        ax = fig.add_subplot()

        (self.dfs['admissions'][(self.dfs['admissions']['AdmissionStartDate']> from_date) & (self.dfs['admissions']['AdmissionStartDate']< to_date)][['AdmissionStartDate']]
        .groupby([self.dfs['admissions'].AdmissionStartDate.dt.year])
        .count()
        .plot(kind="bar", ax=ax))

        ax.set_title("Number of admissions per year")
        ax.set_xlabel("Date")
        ax.set_ylabel("Admission Count")

        return fig, ax


    def admission_time_diff_summary(self):

        fig = plt.figure(figsize=(12,3))
        ax = fig.add_subplot()

        self.dfs['admissions']['AdmissionDiff'] = self.dfs['admissions']['AdmissionEndDate'] - self.dfs['admissions']['AdmissionStartDate']
        self.dfs['admissions']['AdmissionDiff'] = self.dfs['admissions']['AdmissionDiff'] / _np.timedelta64(1,'D')
        self.dfs['admissions']['AdmissionDiff'].plot(kind='hist', ax=ax)

        ax.set_title("Time spent in admission")
        ax.set_xlabel("Time (days)")

        return fig, ax

    def lab_summary(self, from_date=None, to_date=None):
        """[summary]

        Args:
            from_date ([type], optional): [description]. Defaults to None.
            to_date ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]
        """
        self.dfs['labs']['LabDateTime'] = _pd.to_datetime(self.dfs['labs']['LabDateTime'])

        if from_date is None:
            from_date = self.dfs['labs']['LabDateTime'].min()
        else:
            from_date= _dt.datetime.strptime(from_date, '%Y-%m-%d')

        if to_date is None:
            to_date = self.dfs['labs']['LabDateTime'].max()
        else:
            to_date= _dt.datetime.strptime(to_date, '%Y-%m-%d')

        details = self.dfs['labs'][(self.dfs['labs']['LabDateTime']> from_date) & (self.dfs['labs']['LabDateTime']< to_date)].groupby(['LabName', 'LabUnits'])[['LabValue']].describe()

        return details


    def lab_plot(self):
        """Displays a histogram for each lab test seprated by lab type.
        """
        plots = {}

        for lab_type in {x.split(':')[0] for x in self.dfs['labs']['LabName']}:
    
            lab_fig_data = self.dfs['labs'][self.dfs['labs']['LabName'].str.contains(lab_type)]
            
            labs = set(list(lab_fig_data['LabName']))

            n = len(labs)
            j = 4
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

            plots[lab_type] = fig, ax

        return plots


    def personal_plot(self):
        """Displays several barcharts of patient personal information (e.g. gender or race).

        Args:
            self.dfs ([pd.DataFrame]): The dataset to visualise the data from.

        Returns:
            [matplotlib]: plots of patients personal information. 
        """
        categorical_features = ['PatientGender', 'PatientRace', 'PatientMaritalStatus', 'PatientLanguage']
        fig, ax = plt.subplots(1, len(categorical_features), figsize=(10,8))
        for i, categorical_feature in enumerate(self.dfs['patients'][categorical_features]):
            self.dfs['patients'][categorical_feature].value_counts().plot(kind="bar", ax=ax[i]).set_title(categorical_feature)
        
        return fig, ax