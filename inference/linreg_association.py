#!/usr/bin/env python

import numpy as np
import os
import ctypes
from scipy import stats

class LinRegAssociation:


    _fit_once = False


    def __init__(self, geno, expr, min_snps, pval_cutoff = 0.005, cutoff="soft"):
        _path = os.path.dirname(__file__)
        _clib = np.ctypeslib.load_library('../lib/linear_regression.so', _path)
        self._cfstat = _clib.fit
        self._geno = geno
        self._expr = expr
        self._min_snps = min_snps
        self._pval_cutoff = pval_cutoff
        self._cutoff = cutoff


    @property
    def ordered_variables(self):
        self.fit()
        return self._ordered_indices


    @property
    def ordered_pvals(self):
        self.fit()
        return self._pvals[self._ordered_indices]


    @property
    def selected_variables(self):
        self.fit()
        select = np.where(self._pvals < self._pval_cutoff)[0]
        if self._cutoff == "soft":
            nselect = max(select.shape[0], self._min_snps)
        if self._cutoff == "newsoft":
            nselect = max(select.shape[0], 20)
        if self._cutoff == "pval":
            nselect = select.shape[0]
        if self._cutoff == "min":
            nselect = self._min_snps
        if self._cutoff == "hard":
            nselect = min(select.shape[0], self._min_snps)
        return self._ordered_indices[:nselect]


    def fit(self):
        if self._fit_once:
           return
        self._fit_once = True
        self._pvals = self._cpvalcomp(self._geno, self._expr)
        self._ordered_indices = np.argsort(self._pvals)


    def _cpvalcomp(self, geno, expr):
        cfstat = self._cfstat
        cfstat.restype = ctypes.c_int
        cfstat.argtypes = [np.ctypeslib.ndpointer(ctypes.c_double, ndim=1, flags='C_CONTIGUOUS, ALIGNED'),
                           np.ctypeslib.ndpointer(ctypes.c_double, ndim=1, flags='C_CONTIGUOUS, ALIGNED'),
                           ctypes.c_int,
                           ctypes.c_int,
                           ctypes.c_int,
                           np.ctypeslib.ndpointer(ctypes.c_double, ndim=1, flags='C_CONTIGUOUS, ALIGNED')
                          ]
    
        x = geno.reshape(-1,)
        y = expr.reshape(-1,)
        xsize = x.shape[0]
        nsnps = geno.shape[0]
        nsample = geno.shape[1]
        ngene = 1
        fstat = np.zeros(nsnps * ngene)
        success = cfstat(x, y, nsnps, ngene, nsample, fstat)
        pvals = 1 - stats.f.cdf(fstat, 1, nsample-2)
        #pvals = pvals.reshape(nsnps, ngene)
        return pvals
