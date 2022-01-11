import pandas as _pd
import numpy as _np
import datetime as _dt
import matplotlib.pyplot as plt


class SummaryInformation():
    """Contains functions to display relevent general summary statistics.

    """

    def __init__(self, dfs):

        self.dfs = dfs

        self.dfs['admissions']['AdmissionStartDate'] = _pd.to_datetime(
            self.dfs['admissions']['AdmissionStartDate'])
        self.dfs['admissions']['AdmissionEndDate'] = _pd.to_datetime(
            self.dfs['admissions']['AdmissionEndDate'])

        self.dfs['labs']['LabDateTime'] = _pd.to_datetime(
            self.dfs['labs']['LabDateTime'])

    def admission_plot(self, from_date=None, to_date=None):
        """Creates a figure containing time series information on admissions.

        Args:
            from_date (str, optional):
                The date for the plot to begin from (yyyy-mm-dd). Defaults to 
                the minimum date.
            to_date (str, optional):
                The date for the plot to end (yyyy-mm-dd). Defaults to the
                maximum date.

        Returns:
            fig : matplotlib.figure.Figure
            ax : matplotlib.axes.Axes
        """

        if from_date is None:
            from_date = self.dfs['admissions']['AdmissionStartDate'].min()
        else:
            from_date = _dt.datetime.strptime(from_date, '%Y-%m-%d')

        if to_date is None:
            to_date = self.dfs['admissions']['AdmissionStartDate'].max()
        else:
            to_date = _dt.datetime.strptime(to_date, '%Y-%m-%d')

        max_diff = self.dfs['admissions']['AdmissionStartDate'].max().year - \
            self.dfs['admissions']['AdmissionStartDate'].min().year
        diff = ((to_date.year - from_date.year) / max_diff) * 10 + 5

        fig = plt.figure(figsize=(diff, 3))
        ax = fig.add_subplot()

        (self.dfs['admissions'][
            (self.dfs['admissions']['AdmissionStartDate'] > from_date)
            & (self.dfs['admissions']['AdmissionStartDate'] < to_date)
        ][['AdmissionStartDate']]
            .groupby([self.dfs['admissions'].AdmissionStartDate.dt.year])
            .count()
            .plot(kind="bar", ax=ax))

        ax.set_title("Number of admissions per year")
        ax.set_xlabel("Date")
        ax.set_ylabel("Admission Count")

        return fig, ax

    def admission_time_diff_summary(self):
        """Creates a histogram figure containing time spent in admission.

        Returns:
            fig : matplotlib.figure.Figure
            ax : matplotlib.axes.Axes
        """
        fig = plt.figure(figsize=(12, 3))
        ax = fig.add_subplot()

        self.dfs['admissions']['AdmissionDiff'] = \
            self.dfs['admissions']['AdmissionEndDate'] - \
            self.dfs['admissions']['AdmissionStartDate']
        self.dfs['admissions']['AdmissionDiff'] = \
            self.dfs['admissions']['AdmissionDiff'] / \
            _np.timedelta64(1, 'D')
        self.dfs['admissions']['AdmissionDiff'].plot(kind='hist', ax=ax)

        ax.set_title("Time spent in admission")
        ax.set_xlabel("Time (days)")

        return fig, ax

    def lab_summary(self, from_date=None, to_date=None):
        """Creates a table contain summary statistics of lab values for each lab type.

        Args:
            from_date (str, optional):
                The date for the plots to begin from (yyyy-mm-dd). Defaults to
                None (the minimum date).
            to_date (str, optional):
                The date for the plots to end (yyyy-mm-dd). Defaults to None
                (the maximum date).

        Returns:
            pandas.DataFrame
        """
        if from_date is None:
            from_date = self.dfs['labs']['LabDateTime'].min()
        else:
            from_date = _dt.datetime.strptime(from_date, '%Y-%m-%d')

        if to_date is None:
            to_date = self.dfs['labs']['LabDateTime'].max()
        else:
            to_date = _dt.datetime.strptime(to_date, '%Y-%m-%d')

        details = (self.dfs['labs'][
                    (self.dfs['labs']['LabDateTime'] > from_date)
                    & (self.dfs['labs']['LabDateTime'] < to_date)]
                .groupby(['LabName', 'LabUnits'])[['LabValue']]
                .describe())

        return details

    def lab_plot(self):
        """Creates a dictioonary cointaing histogram figures of labvalues for 
        each lab type, with general lab type keys.

        Returns:
            dict{lab type:(fig, ax)}:
                 where 'fig' is a matplotlib.figure.Figure and 'ax' is a 
                 matplotlib.axes.Axes.
        """
        plots = {}

        for lab_type in {x.split(':')[0] for x in self.dfs['labs']['LabName']}:

            lab_fig_data = self.dfs['labs'][self.dfs['labs']
                                            ['LabName'].str.contains(lab_type)]

            labs = set(list(lab_fig_data['LabName']))

            n = len(labs)
            j = 4
            i = round(n / j + .49)

            fig, ax = plt.subplots(i, j, figsize=(28, i * j))

            if i != 1:

                row, col = 0, 0
                for lab in labs:
                    if col == j:
                        col = 0
                        row += 1
                    (lab_fig_data[lab_fig_data['LabName'] ==
                        lab][['LabValue']].plot(kind='hist', grid=True, 
                        ax=ax[row, col], xlabel='Test', ylabel='Test')
                        .set_title(lab))
                    col += 1

                if n % j != 0:
                    for k in range(5 - (n % j)):
                        fig.delaxes(ax[i - 1, j - 1 - k])

            else:

                for i, lab in enumerate(labs):
                    (lab_fig_data[lab_fig_data['LabName'] ==
                        lab][['LabValue']].plot(kind='hist', grid=True, 
                            ax=ax[i], xlabel='Test', ylabel='Test')
                            .set_title(lab))

                if n % j != 0:
                    for k in range(5 - (n % j)):
                        fig.delaxes(ax[j - 1 - k])

            plots[lab_type] = fig, ax

        return plots

    def personal_plot(self):
        """Creates bar chart figures for each categorical variable in 'patients' data.

        Returns:
            fig : matplotlib.figure.Figure
            ax : matplotlib.axes.Axes
        """
        categorical_features = [
            'PatientGender',
            'PatientRace',
            'PatientMaritalStatus',
            'PatientLanguage']
        fig, ax = plt.subplots(1, len(categorical_features), figsize=(10, 8))
        for i, categorical_feature in enumerate(
                self.dfs['patients'][categorical_features]):
            self.dfs['patients'][categorical_feature].value_counts().plot(
                kind="bar", ax=ax[i]).set_title(categorical_feature)

        return fig, ax
