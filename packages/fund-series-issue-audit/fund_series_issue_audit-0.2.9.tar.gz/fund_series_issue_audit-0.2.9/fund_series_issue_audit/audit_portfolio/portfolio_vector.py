from fund_insight_engine import portfolio
from shining_pebbles import get_yesterday
from fund_insight_engine import Portfolio
import pandas as pd

class PortfolioVector:
    def __init__(self, fund_code, date_ref=None):
        self.fund_code = fund_code
        self.date_ref = date_ref if date_ref else get_yesterday()
        self.p = Portfolio(fund_code=self.fund_code, date_ref=self.date_ref)
        self.raw = None
        self.df = None
        self._load_pipeline()

    def get_raw_portfolio(self):
        if self.raw is None:
            raw = self.p.raw
            self.raw = raw
        return self.raw
    
    def get_portfolio(self):
        if self.df is None:
            df = self.p.df
            portfolio = (
                df[['종목', '종목명', '비중']]
                .sort_values(by='비중', ascending=False)
                .rename(columns={'비중': '비중: 자산대비'})
                .set_index('종목')
            )
            self.df = portfolio
        return self.df

    def _load_pipeline(self):
        try:
            self.get_raw_portfolio()
            self.get_portfolio()
            return True
        except Exception as e:
            print(f'PortfolioVector _load_pipeline error: {e}')
            return False
    