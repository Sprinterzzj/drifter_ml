#from mlxtend.evaluate import permutation_test
from statsmodels.tsa import stattools
from statsmodels.stats import diagnostic
from statsmodels.tsa import x13
from statsmodels.tsa import arima_model
import warnings
from collections import namedtuple
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
warnings.filterwarnings("ignore")

class TimeSeriesTests:
    def __init__(self, timeseries):
        self.timeseries = timeseries
        self.model = None
        self.model_result = None
        
    def ad_fuller_test(self):
        result = stattools.adfuller(self.timeseries)
        AdFullerResult = namedtuple('AdFullerResult', 'statistic pvalue')
        return AdFullerResult(result[0], result[1])
    
    def kpss(self):
        result = stattools.kpss(self.timeseries)
        KPSSResult = namedtuple('KPSSResult', 'statistic pvalue')
        return KPSSResult(result[0], result[1])

    def cointegration(self, alt_timeseries):
        result = stattools.coint(self.timeseries, alt_timeseries)
        CointegrationResult = namedtuple('CointegrationResult', 'statistic pvalue')
        return CointegrationResult(result[0], result[1])

    def bds(self):
        result = stattools.bds(self.timeseries)
        BdsResult = namedtuple('BdsResult', 'statistic pvalue')
        return BdsResult(result[0], result[1])
        
    def q_stat(self):
        autocorrelation_coefs = stattools.acf(self.timeseries)
        result = stattools.q_stat(autocorrelation_coefs)
        QstatResult = namedtuple('QstatResult', 'statistic pvalue')
        return QstatResult(result[0], result[1])

    def _evaluate_arima_model(self, X, arima_order):
        # prepare training dataset
        train, test, _, _ = train_test_split(X, np.zeros(X.shape[0]))
        history = list(train)
        # make predictions
        predictions = list()
        for t in range(len(test)):
            model = ARIMA(history, order=arima_order)
            model_fit = model.fit(disp=0)
            yhat = model_fit.forecast()[0]
            predictions.append(yhat)
            history.append(test[t])
        # calculate out of sample error
        error = mean_squared_error(test, predictions)
        return error

    # evaluate combinations of p, d and q values for an ARIMA model
    def generate_model(self):
        best_score, best_cfg = float("inf"), None
        p_values = [0, 1, 2, 4, 6, 8, 10]
        d_values = range(0, 3)
        q_values = range(0, 3)
        for p in p_values:
            for d in d_values:
                for q in q_values:
                    order = (p,d,q)
                    try:
                        mse = self._evaluate_arima_model(self.timeseries, order)
                        if mse < best_score:
                            best_score = mse
                            best_order = order
                    except:
                        continue
        model = ARIMA(self.timeseries, order=best_order)
        model_result = model.fit(disp=0)
        return model, model_result
    
    def acorr_ljungbox(self):
        if self.model is None:
            model, model_result = self.generate_model()
        result = diagnostic.acorr_ljungbox(self.model_result)
        AcorrLjungBoxResult = namedtuple('AcorrLjungBoxResult', 'statistic pvalue')
        return AcorrLjungBoxResult(result[0], result[1])
    
    def acorr_breusch_godfrey(self):
        if self.model is None:
            model, model_result = self.generate_model()
        result = diagnostic.acorr_breusch_godfrey(self.model_result)
        AcorrBreuschGodfreyResult = namedtuple('BreuschGodfreyResult', 'statistic pvalue')
        return AcorrBreuschGodfreyResult(result[0], result[1])

    def het_arch(self):
        if self.model is None:
            model, model_result = self.generate_model()
        result = diagnostic.het_arch(self.model_result)
        HetArchResult = namedtuple('HetArchResult', 'statistic pvalue')
        return HetArchResult(result[0], result[1])

    def breaks_cumsumolsresid(self):
        if self.model is None:
            model, model_result = self.generate_model()
        result = diagnostic.breaks_cusumolsresid(self.model_result)
        BreaksCumSumResult = namedtuple('BreaksCumSumResult', 'statistic pvalue')
        return BreaksCumSumResult(result[0], result[1])
