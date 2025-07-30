import numpy as np
from shining_pebbles import get_yesterday
from .result_application import save_automated_series_issue_audit, load_automated_series_issue_audit_result, get_comparison_of_row_in_df

class SeriesIssueAudit:
    def __init__(self, date_ref=None, option_threshold=0.8):
        self.date_ref = date_ref if date_ref else get_yesterday()
        self.option_threshold = option_threshold
        self._generate = None
        self._load = None

    @property
    def generate(self):
        print(f'date_ref: {self.date_ref}')
        if self._generate is None:
            self._generate = save_automated_series_issue_audit(date_ref=self.date_ref, option_threshold=self.option_threshold)
        return self._generate

    @property
    def load(self):
        print(f'date_ref: {self.date_ref}')
        if self._load is None:
            self._load = load_automated_series_issue_audit_result(date_ref=self.date_ref, option_threshold=self.option_threshold)
        return self._load
    
    def comparison(self, index):
        df = get_comparison_of_row_in_df(self.load, index, date_ref=self.date_ref).copy()
        df['delta'] = df['delta'].map(lambda x: x if x!='-' else np.nan)
        df = df.sort_values(by='delta', ascending=False)
        df['delta'] = df['delta'].fillna('-')
        return df