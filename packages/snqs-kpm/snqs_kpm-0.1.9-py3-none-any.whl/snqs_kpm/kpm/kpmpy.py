import numpy as np
import numpy.linalg as la
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from collections import deque
from multiprocessing import Pool, Process

import sys
import time
from typing import Union, Optional, Callable
from dataclasses import dataclass

@dataclass
class KPM:
    H: sp.csr_matrix
    kernel: str='Jackson'
    N_random: int=20
    N_moments: int=100
    N_division: int=1000
    H_scale: Optional[float]=None
    H_center: Optional[float]=None
    alpha: float=0.4
    info: bool=True
    seed: int=42
    lorentz_lambda: float=3. 

    def __post_init__(self):
        assert self.N_moments%2 == 0, 'Error: N_moments must be even.'
        assert self.N_moments > 3, 'Error: N_moments must be grater than 3.'
        assert self.alpha > 0., 'Error: alpha must be positive.'

        self.shape = self.H.shape
        self.N_site = self.shape[0]
        self.dtype = self.H.dtype

        self.H_tilde = self._prep_Hamiltonian()

        if self.kernel == 'Jackson':
            self.kernel = self._Jackson()
        elif self.kernel == 'Dirichlet':
            self.kernel = self._Dirichlet()
        elif self.kernel == 'Lorentz':
            self.kernel = self._Lorentz()
        else:
            print("Error: kernel must be 'Jackson', 'Lorentz' or 'Dirichlet'.")
            sys.exit()


    # =======================================================================================================
    def _prep_Hamiltonian(self):
        if self.H_center is not None:
            H_tilde = self.H - sp.diags([self.H_center], shape=self.shape)
        else:
            H_tilde = self.H.copy()
            self.H_center = 0.

        if self.H_scale is None:
            s = time.time()
            Emax, _ = spla.eigsh(H_tilde, k=1)
            self.H_scale = np.abs(Emax[0])
            # if self.info:
                # print('maximum eigenvalue = {:.4g}, computation time = {:.4g} [s]'.format(self.H_scale, time.time()-s))
        self.H_scale *= 1. + self.alpha

        return H_tilde /self.H_scale


    def _Jackson(self):
        N = self.N_moments
        phase = np.pi /(N+1)
        g = [
            1/(N+1) *( (N-n+1)*np.cos(n*phase) + np.sin(n*phase) /np.tan(phase) ) for n in range(N)
        ]
        return np.array(g, dtype=self.dtype)

    def _Dirichlet(self):
        return np.ones(self.N_moments, dtype=self.dtype)

    def _Lorentz(self):
        N = self.N_moments
        lamb = self.lorentz_lambda
        g = [
            np.sinh(lamb *(1 - n/N)) /np.sinh(lamb) for n in range(N)
        ]
        return np.array(g, dtype=self.dtype)


    # =======================================================================================================
    def _get_moments(self, local=False, site=0):
        if local:
            a0 = np.zeros(self.N_site, dtype=self.dtype)
            a0[site] = 1.
        else:
            a0 = self.rng.normal(size=self.N_site)
            a0 /= la.norm(a0)
        a1 = self.H_tilde @a0
        a = deque([a0,a1])
        mu_list = np.empty(self.N_moments, dtype=self.dtype)
        mu_list[0] = 1.
        mu_list[1] = np.conjugate(a0) @a1
        for i in range(1, self.N_moments//2):
            # a: [a_n-1, a_n] -> [a_n-1, a_n, a_n+1] -> [a_n, a_n+1]
            a.append( 2.*(self.H_tilde @a[1]) - a[0] )
            a.popleft()
            mu_list[2*i] = 2.*(np.conjugate(a[0]) @a[0]) - mu_list[0]
            mu_list[2*i+1] = 2.*(np.conjugate(a[1]) @a[0]) - mu_list[1]
        return mu_list

    def _get_moments_w_operator(self, A, local=False, site=0):
        if local:
            a0 = np.zeros(self.N_site, dtype=self.dtype)
            a0[site] = 1.
        else:
            a0 = self.rng.normal(size=self.N_site)
            a0 /= la.norm(a0)
        a1 = self.H_tilde @a0
        a = deque([a0,a1])
        a0_bra = np.conjugate(a0).T
        mu_list = np.empty(self.N_moments, dtype=self.dtype)
        mu_list[0] = a0_bra @A @a0
        mu_list[1] = a0_bra @A @a1
        for i in range(2, self.N_moments):
            # a: [a_n-1, a_n] -> [a_n-1, a_n, a_n+1] -> [a_n, a_n+1]
            a.append( 2.*(self.H_tilde @a[1]) - a[0] )
            a.popleft()
            mu_list[i] = a0_bra @A @a[1] 
        return mu_list

    def _get_moments_ij(self, i, j):
        a0 = np.zeros(self.N_site, dtype=self.dtype)
        a0[i] = 1.
        b = np.zeros(self.N_site, dtype=self.dtype)
        b[j] = 1.
        a1 = self.H_tilde @a0
        a = deque([a0,a1])
        b_bra = np.conjugate(b).T
        mu_list = np.empty(self.N_moments, dtype=self.dtype)
        mu_list[0] = b_bra @a0
        mu_list[1] = b_bra @a1
        for i in range(1, self.N_moments//2):
            # a: [a_n-1, a_n] -> [a_n-1, a_n, a_n+1] -> [a_n, a_n+1]
            a.append( 2.*(self.H_tilde @a[1]) - a[0] )
            a.popleft()
            mu_list[i] = b_bra @a[1] 
        return mu_list
    
    def _get_moments_dynamical_correlation_at_zero_temperature_A_B(self, dip, psi0, local=False, site=0):
        a0 = dip@psi0 # vec
        a1 = self.H_tilde @a0 #vec
        a = deque([a0,a1])
        mu_list = np.empty(self.N_moments, dtype=self.dtype)
        mu_list[0] = np.conjugate(a0) @a0 #num
        mu_list[1] = np.conjugate(a0) @a1 #num
        for i in range(1, self.N_moments//2):
            # a: [a_n-1, a_n] -> [a_n-1, a_n, a_n+1] -> [a_n, a_n+1]
            a.append( 2.*(self.H_tilde @a[1]) - a[0] ) #bottelneck part
            a.popleft()
            mu_list[2*i] = 2.*(np.conjugate(a[0]) @a[0]) - mu_list[0]
            mu_list[2*i+1] = 2.*(np.conjugate(a[1]) @a[0]) - mu_list[1]
        return mu_list


    def _get_spectrum(self, x):
        if x is None:
            x = np.linspace(-0.99, 0.99, self.N_division)
        else:
            assert len(x) == self.N_division, 'Error: length of x must be {}'.format(self.N_division)
            x = (x - self.H_center) /self.H_scale
            assert np.max(np.abs(x)) < 0.995, 'Error: The range of x is not appropriate.'
        
        T = deque([
            np.ones(self.N_division, dtype=self.dtype), 
            x.copy()
        ])
        spec = self.moments[0] *self.kernel[0] *T[0] \
            + 2 *self.moments[1] *self.kernel[1] *T[1]
        for mu, g in zip(self.moments[2:], self.kernel[2:]):
            T.append( 2 *x *T[1] - T[0] )
            T.popleft()
            spec += 2 *mu *g *T[1]
        spec /= np.pi *np.sqrt(1 - x*x)
        return spec
        

    # =======================================================================================================
    def get_DOS(self, x=None):
        self.rng = np.random.default_rng(self.seed)
        self.moments = np.zeros(self.N_moments, dtype=self.dtype)
        for _ in range(self.N_random):
            self.moments += self._get_moments()
        self.moments /= self.N_random
        DOS = self._get_spectrum(x)
        if self.dtype == np.complex128:
            print('maximum of imaginaly part of DOS = {:.3g}'.format(np.max(np.imag(DOS))))
            DOS = np.real(DOS)
        return DOS

    def get_LDOS(self, x=None, site=0):
        self.moments = self._get_moments(local=True, site=site)
        LDOS = self._get_spectrum(x)
        if self.dtype == np.complex128:
            if np.max(np.imag(LDOS)) > 1e-8:
                print('maximum of imaginaly part of LDOS = {:.3g}'.format(np.max(np.imag(LDOS))))
            LDOS = np.real(LDOS)
        return LDOS
    
    def get_corr_DOS(self, dip, psi0, x=None):
        self.moments = self._get_moments_dynamical_correlation_at_zero_temperature_A_B(dip,psi0)
        DOS = self._get_spectrum(x)
        if self.dtype == np.complex128:
            # print('maximum of imaginaly part of DOS = {:.3g}'.format(np.max(np.imag(DOS))))
            DOS = np.real(DOS)
        return DOS
    
    def get_corr_DOS_input_moments(self, moments, x=None):
        self.moments = moments
        DOS = self._get_spectrum(x)
        if self.dtype == np.complex128:
            # print('maximum of imaginaly part of DOS = {:.3g}'.format(np.max(np.imag(DOS))))
            DOS = np.real(DOS)
        return DOS

    def get_spectrum_w_operator(self, A, x=None, local=False, site=0):
        assert A.shape == self.shape, 'Shape of A doesn\'t match. A.shape must be {}'.format(self.shape) 
        
        if local:
            self.moments = self._get_moments_w_operator(A, local=True, site=site)
        else:
            self.rng = np.random.default_rng(self.seed)
            self.moments = np.zeros(self.N_moments, dtype=self.dtype)
            for _ in range(self.N_random):
                self.moments += self._get_moments_w_operator(A)
            self.moments /= self.N_random

        spec = self._get_spectrum(x)
        return spec